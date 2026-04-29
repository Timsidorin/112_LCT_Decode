import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status
from openai import OpenAI

from core.config import configs
from core.logging_config import logger

# Максимальное количество страниц PDF для обработки
PDF_MAX_PAGES = 60

# DPI для рендеринга страниц PDF в PNG (150 — баланс качество/скорость)
PDF_RENDER_DPI = 150

PDF_PAGE_ANALYSIS_PROMPT = """
Ты анализируешь СКРИНШОТ интерфейса программного обеспечения, извлеченный из инструкции.
Твоя задача: найти ОДНО целевое действие на этом скриншоте.

Контекстная информация из текста инструкции (рядом с картинкой):
{page_text}

Инструкция для тебя:
1. Определи, какое действие нужно выполнить, глядя на скриншот и читая контекст.
2. Найди UI-элемент (кнопку, поле ввода и т.д.) на этом скриншоте.
3. Сформулируй краткое название и инструкцию на русском языке.
4. Верни bbox этого элемента ОТНОСИТЕЛЬНО ЭТОГО СКРИНШОТА (в нормализованных координатах 0..1).

Верни только JSON:
{{
  "title": "Название действия",
  "instruction_md": "Инструкция...",
  "interaction": {{
    "type": "left_click|text_input|key_chord|hover",
    "bbox": [x1, y1, x2, y2], // [xmin, ymin, xmax, ymax] 0..1 относительно картинки
    "expected_text": null
  }}
}}

Важно:
- Если элементов несколько — выбери самый важный, о котором говорится в тексте.
- Будь предельно точен в координатах bbox.
"""


@dataclass
class PdfStepData:
    """Результат VLM-анализа одной картинки из PDF."""

    page_number: int
    instruction_md: str
    step_title: str
    bbox: List[float]
    page_bytes: bytes       # Чистое изображение скриншота
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
    allowed = {"left_click", "right_click", "double_click", "hover", "text_input", "key_chord"}
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
        self.client = OpenAI(
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

        results: List[PdfStepData] = []
        zoom = PDF_RENDER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_number = page_idx + 1
            
            images_on_page = page.get_images(full=True)
            if not images_on_page:
                continue

            logger.info(f"[PDF AI] Страница {page_number}: найдено {len(images_on_page)} объектов изображений")

            # Каждое изображение может быть одним шагом
            for img_info in images_on_page:
                xref = img_info[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                
                # Работаем с первым вхождением изображения на странице
                rect = rects[0]
                
                # Фильтр на мелкие элементы (иконки, линии) — обычно скриншот крупный
                if rect.width < 100 or rect.height < 50:
                    continue

                # Извлекаем текст рядом с картинкой (±150 пикселей по вертикали)
                context_rect = fitz.Rect(0, max(0, rect.y0 - 150), page.rect.width, min(page.rect.height, rect.y1 + 150))
                context_text = page.get_text("text", clip=context_rect).strip()

                # Рендерим именно область картинки
                try:
                    pix = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
                    png_bytes = pix.tobytes("png")
                    img_width = pix.width
                    img_height = pix.height
                except Exception as e:
                    logger.warning(f"[PDF AI] Стр {page_number}: ошибка рендеринга картинки {xref} — {e}")
                    continue

                # Анализируем через VLM
                step_data = await self._analyze_image_object(
                    page_number=page_number,
                    png_bytes=png_bytes,
                    context_text=context_text,
                    width=img_width,
                    height=img_height
                )
                
                if step_data:
                    results.append(step_data)

        doc.close()
        logger.info(f"[PDF AI] Найдено {len(results)} шагов")
        return results

    async def _analyze_image_object(
        self,
        page_number: int,
        png_bytes: bytes,
        context_text: str,
        width: int,
        height: int
    ) -> Optional[PdfStepData]:
        """Анализирует ОДИН конкретный скриншот ПО."""
        try:
            base64_image = base64.b64encode(png_bytes).decode("utf-8")
            prompt = PDF_PAGE_ANALYSIS_PROMPT.format(
                page_text=context_text[:3000] if context_text else "Контекст не найден."
            )

            completion = self.client.chat.completions.create(
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
                if not match: return None
                data = json.loads(match.group(0))

            title = str(data.get("title") or "").strip()
            instruction_md = str(data.get("instruction_md") or "").strip()
            if not title and not instruction_md: return None

            inter = data.get("interaction") or data
            itype = _normalize_interaction_type(str(inter.get("type") or "left_click"))
            
            raw_bbox = inter.get("bbox")
            bbox = self._coerce_bbox(raw_bbox)
            if not bbox: return None
            
            bbox = self._normalize_bbox_scale(bbox)
            x1, y1, x2, y2 = bbox
            bbox = [max(0.0, min(1.0, b)) for b in [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]]

            expected_text = None
            if itype == "text_input":
                expected_text = str(inter.get("expected_text") or "").strip() or None

            return PdfStepData(
                page_number=page_number,
                instruction_md=instruction_md or title or "Выполните действие.",
                step_title=title or f"Шаг на стр. {page_number}",
                bbox=bbox,
                page_bytes=png_bytes,
                page_width=width,
                page_height=height,
                action_type_key=itype,
                expected_text=expected_text
            )

        except Exception as e:
            logger.error(f"[PDF AI] Ошибка VLM для картинки: {e}")
            return None

    def _coerce_bbox(self, raw: Any) -> Optional[List[float]]:
        if isinstance(raw, list) and len(raw) == 4:
            try: return [float(v) for v in raw]
            except: return None
        if not isinstance(raw, dict): return None
        
        # Обработка словаря x1, y1, x2, y2 или x, y, w, h
        def _get(*keys):
            for k in keys:
                if k in raw: return raw[k]
            return None
            
        coords = [_get("x1", "xmin", "left"), _get("y1", "ymin", "top"), _get("x2", "xmax", "right"), _get("y2", "ymax", "bottom")]
        if None not in coords:
            return [float(c) for c in coords]
            
        x, y, w, h = _get("x"), _get("y"), _get("w", "width"), _get("h", "height")
        if None not in (x, y, w, h):
            return [float(x), float(y), float(x)+float(w), float(y)+float(h)]
        return None

    def _normalize_bbox_scale(self, bbox: List[float]) -> List[float]:
        if not bbox or len(bbox) != 4: return bbox
        if all(0.0 <= b <= 100.0 for b in bbox) and any(b > 1.0 for b in bbox):
            return [b / 100.0 for b in bbox]
        return bbox
