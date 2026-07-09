import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from openai import AsyncOpenAI

from core.config import configs
from core.logging_config import logger

# Максимальное количество страниц PDF для обработки
PDF_MAX_PAGES = 60

# DPI для рендеринга страниц PDF в PNG (200 — хорошее качество для VLM)
PDF_RENDER_DPI = 200

# Минимальный размер изображения на странице (фильтр иконок)
PDF_MIN_IMG_WIDTH = 120
PDF_MIN_IMG_HEIGHT = 80

PDF_PAGE_ANALYSIS_PROMPT = """
Ты анализируешь СКРИНШОТ программного обеспечения из обучающей инструкции.
Твоя задача: определить ОДНО конкретное действие пользователя и точно разметить его область.

Контекст из текста инструкции рядом со скриншотом:
{page_text}

Алгоритм:
1. Прочитай контекст — он описывает что нужно сделать.
2. Найди соответствующий UI-элемент на скриншоте (кнопку, поле, пункт меню, иконку).
3. Обведи МИНИМАЛЬНЫЙ bbox вокруг этого элемента.
4. Сформулируй title начиная с глагола действия.

Верни ТОЛЬКО JSON без markdown-блоков и комментариев:
{{
  "title": "[Глагол] [объект] — например: Нажать кнопку Сохранить",
  "instruction_md": "Чёткая инструкция для пользователя на русском (1-2 предложения).",
  "interaction": {{
    "type": "left_click|right_click|double_click|text_input|key_chord|hover",
    "bbox": [x1, y1, x2, y2],
    "expected_text": null
  }}
}}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
- title ВСЕГДА начинается с глагола: "Нажать", "Выбрать", "Ввести", "Открыть", "Установить", "Снять".
- bbox нормализован 0..1 относительно данного скриншота. x1<x2, y1<y2.
- bbox должен быть МИНИМАЛЬНЫМ вокруг элемента (только кнопка, только поле, только строка меню).
- Запрещено: bbox занимает более 60% ширины или высоты скриншота если цель — один элемент.
- type строго по характеру действия: текстовый ввод → text_input + expected_text.
- Если действие из контекста неясно или элемент не виден — верни пустой JSON {{}}.
"""

PDF_FULL_PAGE_ANALYSIS_PROMPT = """
Ты анализируешь ПОЛНУЮ СТРАНИЦУ инструкции по работе с программным обеспечением.
На странице нет отдельных скриншотов, но может быть текстовое описание действий.

Контекст страницы:
{page_text}

Задача: определи главное действие пользователя, описанное на этой странице.
Если на странице виден UI (кнопки, поля, меню) — найди целевой элемент и его bbox.
Если страница чисто текстовая без UI — верни пустой JSON {{}}.

Верни ТОЛЬКО JSON без markdown:
{{
  "title": "[Глагол] [объект]",
  "instruction_md": "Инструкция на русском (1-2 предложения).",
  "interaction": {{
    "type": "left_click|right_click|double_click|text_input|key_chord|hover",
    "bbox": [x1, y1, x2, y2],
    "expected_text": null
  }}
}}
"""


@dataclass
class PdfStepData:
    """Результат VLM-анализа одной картинки из PDF."""

    page_number: int
    instruction_md: str
    step_title: str
    bbox: List[float]
    page_bytes: bytes
    page_width: int
    page_height: int
    action_type_key: str
    expected_text: Optional[str] = None
    key_chord: Optional[List[str]] = None


def _normalize_interaction_type(raw: str) -> str:
    r = (raw or "left_click").strip().lower()
    aliases = {
        "leftclick": "left_click",
        "left_click": "left_click",
        "rightclick": "right_click",
        "right_click": "right_click",
        "doubleclick": "double_click",
        "double_click": "double_click",
        "input_text": "text_input",
        "text_input": "text_input",
        "key_press": "key_chord",
        "keychord": "key_chord",
        "key_chord": "key_chord",
        "hover": "hover",
        "click": "left_click",
        "left": "left_click",
        "right": "right_click",
        "double": "double_click",
        "type_text": "text_input",
        "typing": "text_input",
        "input": "text_input",
        "keyboard": "key_chord",
        "hotkey": "key_chord",
    }
    if r in aliases:
        return aliases[r]
    allowed = {
        "left_click",
        "right_click",
        "double_click",
        "hover",
        "text_input",
        "key_chord",
    }
    return r if r in allowed else "left_click"


def _normalize_key_chord(raw: Any) -> Optional[List[str]]:
    if raw is None:
        return None
    if isinstance(raw, str):
        parts = re.split(r"[\s+,]+", raw.strip().lower())
        return [p for p in parts if p]
    if isinstance(raw, list):
        out = []
        for x in raw:
            if x is None:
                continue
            s = str(x).strip().lower()
            if s:
                out.append(s)
        return out or None
    return None


class PdfAiService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=configs.AI_API_KEY,
            base_url=configs.AI_BASE_URL,
            timeout=httpx.Timeout(300.0, connect=30.0),
            max_retries=2,
        )
        self.model = configs.AI_MODEL

    async def analyze_pdf(self, pdf_bytes: bytes) -> List[PdfStepData]:
        try:
            import fitz
        except ImportError:
            raise HTTPException(500, detail="PyMuPDF не установлен.")

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise HTTPException(422, detail=f"Ошибка открытия PDF: {e}")

        total_pages = min(len(doc), PDF_MAX_PAGES)
        logger.info(f"[PDF AI] Извлечение изображений из {total_pages} страниц")

        zoom = PDF_RENDER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        # 1. Извлекаем все изображения и тексты (синхронно, быстро)
        analysis_tasks = []

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_number = page_idx + 1

            images_on_page = page.get_images(full=True)
            page_text_full = page.get_text("text").strip()

            if not images_on_page:
                if not page_text_full:
                    logger.info(f"[PDF AI] Страница {page_number}: пустая, пропуск")
                    continue
                logger.info(
                    f"[PDF AI] Страница {page_number}: нет изображений, рендерим всю страницу"
                )
                try:
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    analysis_tasks.append({
                        "page_number": page_number,
                        "png_bytes": pix.tobytes("png"),
                        "context_text": page_text_full,
                        "width": pix.width,
                        "height": pix.height,
                        "full_page": True,
                        "fallback": False
                    })
                except Exception as e:
                    logger.warning(f"[PDF AI] Стр {page_number}: ошибка рендеринга страницы — {e}")
                continue

            logger.info(
                f"[PDF AI] Страница {page_number}: найдено {len(images_on_page)} объектов изображений"
            )

            has_valid_images = False
            for img_info in images_on_page:
                xref = img_info[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue

                rect = rects[0]
                if rect.width < PDF_MIN_IMG_WIDTH or rect.height < PDF_MIN_IMG_HEIGHT:
                    continue

                context_rect = fitz.Rect(
                    0,
                    max(0, rect.y0 - 200),
                    page.rect.width,
                    min(page.rect.height, rect.y1 + 200),
                )
                context_text = page.get_text("text", clip=context_rect).strip()
                if not context_text:
                    context_text = page_text_full

                try:
                    pix = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
                    analysis_tasks.append({
                        "page_number": page_number,
                        "png_bytes": pix.tobytes("png"),
                        "context_text": context_text,
                        "width": pix.width,
                        "height": pix.height,
                        "full_page": False,
                        "fallback": False
                    })
                    has_valid_images = True
                except Exception as e:
                    logger.warning(f"[PDF AI] Стр {page_number}: ошибка рендеринга картинки {xref} — {e}")

            if not has_valid_images and page_text_full:
                logger.info(f"[PDF AI] Страница {page_number}: изображения не валидны, fallback — вся страница")
                try:
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    analysis_tasks.append({
                        "page_number": page_number,
                        "png_bytes": pix.tobytes("png"),
                        "context_text": page_text_full,
                        "width": pix.width,
                        "height": pix.height,
                        "full_page": True,
                        "fallback": True
                    })
                except Exception as e:
                    logger.warning(f"[PDF AI] Стр {page_number}: ошибка fallback рендеринга — {e}")

        doc.close()

        # 2. Выполняем запросы к VLM конкурентно (с ограничением параллелизма, чтобы не перегрузить API)
        import asyncio

        results: List[PdfStepData] = []
        semaphore = asyncio.Semaphore(40)  # Максимум 40 параллельных запросов

        async def _analyze_with_semaphore(kwargs):
            fallback = kwargs.pop("fallback")
            async with semaphore:
                step_data = await self._analyze_image_object(**kwargs)
                return {"page_number": kwargs["page_number"], "step_data": step_data, "fallback": fallback}

        logger.info(f"[PDF AI] Запуск параллельного анализа {len(analysis_tasks)} изображений...")
        tasks_futures = [_analyze_with_semaphore(kwargs) for kwargs in analysis_tasks]
        
        analysis_results = await asyncio.gather(*tasks_futures)

        # 3. Собираем результаты, учитывая fallback логику
        page_has_results = {}
        for res in analysis_results:
            pn = res["page_number"]
            sd = res["step_data"]
            fb = res["fallback"]
            
            if sd:
                # Если это fallback результат, добавляем его только если для страницы еще нет обычных результатов
                if fb:
                    if not page_has_results.get(pn, False):
                        results.append(sd)
                        page_has_results[pn] = True
                else:
                    results.append(sd)
                    page_has_results[pn] = True

        # Сортируем результаты по номеру страницы, так как gather может вернуть их не в порядке добавления
        results.sort(key=lambda x: x.page_number)

        logger.info(f"[PDF AI] Найдено {len(results)} шагов")
        return results

    async def _analyze_image_object(
        self,
        page_number: int,
        png_bytes: bytes,
        context_text: str,
        width: int,
        height: int,
        full_page: bool = False,
    ) -> Optional[PdfStepData]:
        """Анализирует ОДИН конкретный скриншот ПО."""
        import asyncio
        import base64
        import re
        import json
        
        try:
            base64_image = base64.b64encode(png_bytes).decode("utf-8")
            template = (
                PDF_FULL_PAGE_ANALYSIS_PROMPT if full_page else PDF_PAGE_ANALYSIS_PROMPT
            )
            prompt = template.format(
                page_text=context_text[:4000] if context_text else "Контекст не найден."
            )

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=1000,
                temperature=0.0,
            )

            raw_response = completion.choices[0].message.content

            # Парсим результат
            text = raw_response.strip()
            code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            if code_block:
                text = code_block.group(1).strip()

            try:
                data = json.loads(text)
            except:
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if not match:
                    return None
                data = json.loads(match.group(0))

            # Пустой ответ (модель не нашла действие)
            if not data:
                logger.info(f"[PDF AI] Стр {page_number}: модель не нашла действие")
                return None

            title = str(data.get("title") or "").strip()
            instruction_md = str(data.get("instruction_md") or "").strip()
            if not title and not instruction_md:
                return None

            inter = data.get("interaction") or data
            itype = _normalize_interaction_type(str(inter.get("type") or "left_click"))

            raw_bbox = inter.get("bbox")
            bbox = self._coerce_bbox(raw_bbox)
            if not bbox:
                return None

            bbox = self._normalize_bbox_scale(bbox)
            x1, y1, x2, y2 = bbox
            bbox = [
                max(0.0, min(1.0, b))
                for b in [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
            ]

            # Фильтр слишком маленьких и слишком больших bbox
            bw = bbox[2] - bbox[0]
            bh = bbox[3] - bbox[1]
            if bw < 0.005 or bh < 0.005:
                logger.warning(
                    f"[PDF AI] Стр {page_number}: bbox слишком мал ({bw:.3f}x{bh:.3f}), пропуск"
                )
                return None
            if bw > 0.95 or bh > 0.95:
                logger.warning(
                    f"[PDF AI] Стр {page_number}: bbox слишком велик ({bw:.3f}x{bh:.3f}), пропуск"
                )
                return None

            expected_text = None
            key_chord = None
            if itype == "text_input":
                expected_text = str(inter.get("expected_text") or "").strip() or None
            elif itype == "key_chord":
                from services.video_ai_service import _normalize_key_chord as _nkc

                key_chord = _nkc(inter.get("key_chord"))

            return PdfStepData(
                page_number=page_number,
                instruction_md=instruction_md or title or "Выполните действие.",
                step_title=title or f"Шаг на стр. {page_number}",
                bbox=bbox,
                page_bytes=png_bytes,
                page_width=width,
                page_height=height,
                action_type_key=itype,
                expected_text=expected_text,
                key_chord=key_chord,
            )

        except Exception as e:
            import traceback
            logger.error(f"[PDF AI] Ошибка VLM для картинки: {e}\n{traceback.format_exc()}")
            return None

    def _coerce_bbox(self, raw: Any) -> Optional[List[float]]:
        if isinstance(raw, list) and len(raw) == 4:
            try:
                return [float(v) for v in raw]
            except:
                return None
        if not isinstance(raw, dict):
            return None

        # Обработка словаря x1, y1, x2, y2 или x, y, w, h
        def _get(*keys):
            for k in keys:
                if k in raw:
                    return raw[k]
            return None

        coords = [
            _get("x1", "xmin", "left"),
            _get("y1", "ymin", "top"),
            _get("x2", "xmax", "right"),
            _get("y2", "ymax", "bottom"),
        ]
        if None not in coords:
            return [float(c) for c in coords]

        x, y, w, h = _get("x"), _get("y"), _get("w", "width"), _get("h", "height")
        if None not in (x, y, w, h):
            return [float(x), float(y), float(x) + float(w), float(y) + float(h)]
        return None

    def _normalize_bbox_scale(self, bbox: List[float]) -> List[float]:
        if not bbox or len(bbox) != 4:
            return bbox
        if all(0.0 <= b <= 100.0 for b in bbox) and any(b > 1.0 for b in bbox):
            return [b / 100.0 for b in bbox]
        return bbox
