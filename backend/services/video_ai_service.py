import base64
import json
import os
import re
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import httpx
import numpy as np
from fastapi import HTTPException, UploadFile, status
from openai import OpenAI

from core.config import configs
from core.logging_config import logger

ANALYSIS_PROMPT = """
Ты анализируешь СКРИНКАСТ (запись экрана) обучающего видео по работе с программным обеспечением.
Твоя задача: составить точный пошаговый JSON для интерактивного тренинга-симулятора.

Для каждого видимого действия пользователя (клик, двойной клик, правый клик, ввод текста, горячие клавиши) создай отдельный шаг.

Верни ТОЛЬКО JSON без каких-либо пояснений или markdown-блоков:
{
  "steps": [
    {
      "timecode_before": "MM:SS.f",
      "timecode_after": "MM:SS.f",
      "title": "[Глагол действия] [объект действия]",
      "instruction_md": "Чёткая инструкция для пользователя (1-3 предложения на русском).",
      "interaction": {
        "type": "left_click|right_click|double_click|hover|text_input|key_chord",
        "bbox": [x1, y1, x2, y2],
        "expected_text": null,
        "key_chord": null
      }
    }
  ]
}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:

1. title — ВСЕГДА начинается с глагола действия: "Нажать кнопку Сохранить", "Ввести имя пользователя", "Выбрать пункт меню Файл", "Нажать Ctrl+S". НЕ пиши абстрактно "Шаг 1" или "Действие".

2. timecode_before — точный таймкод кадра непосредственно ПЕРЕД действием (интерфейс стабилен, курсор виден, целевой элемент виден). Бери кадр максимально близко к моменту действия — за 0.1-0.3 секунды до клика.

3. timecode_after — точный таймкод первого стабильного кадра ПОСЛЕ завершения действия (UI изменился, анимации/загрузка закончились). Если UI не изменился — всё равно укажи кадр через 0.5 секунды после действия.

4. bbox строго нормализован 0..1 относительно ПОЛНОГО кадра видео. Обводи МИНИМАЛЬНЫЙ прямоугольник вокруг кликаемого элемента:
   - Кнопка: только сама кнопка (не панель)
   - Поле ввода: только поле (не форма)
   - Пункт меню: только строка меню
   - Иконка: только иконка
   - ЗАПРЕЩЕНО: bbox шире 0.5 ширины экрана если цель — один элемент

5. type — строго по фактическому действию:
   - одиночный клик → left_click
   - двойной клик → double_click  
   - правый клик → right_click
   - наведение без клика → hover
   - ввод текста → text_input (обязательно expected_text)
   - горячие клавиши → key_chord (обязательно key_chord: ["ctrl","s"])

6. Для text_input: expected_text — ТОЧНЫЙ введённый текст как на экране.

7. Для key_chord: key_chord — массив клавиш латиницей ["ctrl","s"], ["alt","f4"] и т.д.

8. Не создавай шаг если: bbox неизвестен, действие неразличимо, это просто прокрутка без цели.

9. Таймкоды с десятыми секунды: "1:05.3", "0:32.7".
"""

FALLBACK_ANALYSIS_PROMPT = """
Проанализируй видео-скринкаст и создай JSON шагов интерактивного тренинга.
Верни ТОЛЬКО JSON без markdown и комментариев:

{
  "steps": [
    {
      "timecode_before": "MM:SS",
      "timecode_after": "MM:SS",
      "title": "[Глагол] [объект] — например: Нажать кнопку ОК",
      "instruction_md": "Краткая инструкция на русском языке.",
      "interaction": {
        "type": "left_click|right_click|double_click|hover|text_input|key_chord",
        "bbox": [x1, y1, x2, y2],
        "expected_text": null,
        "key_chord": null
      }
    }
  ]
}

Правила:
- Каждый шаг = одно чёткое пользовательское действие (клик, ввод, хоткей).
- title начинается с глагола: "Нажать", "Выбрать", "Ввести", "Открыть".
- timecode_before — кадр непосредственно перед действием (стабильный, интерфейс виден).
- timecode_after — первый стабильный кадр после изменения UI.
- bbox 0..1, минимальный вокруг целевого элемента, x1<x2, y1<y2.
- text_input → expected_text обязателен.
- key_chord → key_chord (массив) обязателен.
- steps непустой.
"""

REPAIR_JSON_PROMPT = """
Предыдущий ответ не удалось разобрать как JSON. Проанализируй то же видео ещё раз.
Верни ТОЛЬКО один JSON-объект без markdown и текста до/после:

{"steps":[{"timecode_before":"M:SS","timecode_after":"M:SS","title":"…","instruction_md":"…","interaction":{"type":"left_click","bbox":[0.1,0.2,0.15,0.25]}}]}

Обязательно: timecode_before, timecode_after, title, instruction_md, interaction.type, interaction.bbox как четыре числа 0..1 (доли ширины/высоты кадра).
Минимум один шаг. bbox строго внутри 0..1.
"""

# Максимальная сторона кадра при масштабировании
MAX_FRAME_SIDE = 1280
# Целевой FPS для сжатого видео
COMPRESSED_FPS = 2
# Качество JPEG при сжатии кадров (0-100)
JPEG_QUALITY = 60


@dataclass
class VideoStepData:
    """Результат AI-анализа одного шага из видео (симулятор)."""

    timecode: str
    instruction_md: str
    step_title: str
    bbox: List[float]
    frame_bytes: bytes
    frame_width: int
    frame_height: int
    action_type_key: str
    expected_text: Optional[str] = None
    key_chord: Optional[List[str]] = None
    timecode_before: Optional[str] = None
    timecode_after: Optional[str] = None
    after_frame_bytes: Optional[bytes] = None


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


class VideoCompressor:
    """
    Отвечает за сжатие видео до допустимого размера для API.
    
    Стратегия (применяется последовательно до достижения лимита):
    1. Снижение FPS
    2. Масштабирование разрешения
    3. Снижение качества JPEG
    4. Дополнительное снижение FPS
    """

    def __init__(self, max_base64_bytes: int) -> None:
        self.MAX_BASE64_BYTES = max(1, int(max_base64_bytes))

    @staticmethod
    def _estimate_b64_size(file_path: str) -> int:
        return (os.path.getsize(file_path) * 4) // 3

    def build_analysis_proxy(self, video_path: str) -> str:
        """
        Облегчённая копия для VL: ограничение по стороне и FPS в файле.
        Длительность и таймкоды в секундах совпадают с оригиналом (только прореживание кадров).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось открыть видео для подготовки анализа",
            )
        src_fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        cap.release()

        want_fps = max(1, int(configs.AI_VIDEO_ANALYSIS_ENCODE_FPS))
        target_fps = min(want_fps, max(1, int(round(src_fps))))
        max_side = max(320, int(configs.AI_VIDEO_ANALYSIS_MAX_SIDE))
        jpeg_q = max(30, min(95, int(configs.AI_VIDEO_ANALYSIS_JPEG_QUALITY)))

        out = self._encode_video(
            video_path,
            target_fps=target_fps,
            max_side=max_side,
            jpeg_quality=jpeg_q,
        )
        est_kb = self._estimate_b64_size(out) // 1024
        logger.info(
            f"Анализ-прокси для AI: ~{est_kb}KB base64, "
            f"{max_side}px max, {target_fps}fps в файле (исходник был {src_fps:.1f}fps)"
        )
        return out

    def compress_video(self, video_path: str) -> Tuple[str, float, float]:
        """
        Сжимает видео до допустимого размера.
        
        Returns:
            (compressed_path, original_fps, compressed_fps)
            compressed_path может совпадать с video_path если сжатие не нужно.
        """
        original_b64_size = self._estimate_b64_size(video_path)

        soft = max(1, int(getattr(configs, "AI_VIDEO_SOFT_BASE64_BYTES", 18_000_000)))
        effective_limit = min(self.MAX_BASE64_BYTES, soft)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось открыть видеофайл для сжатия",
            )

        original_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if original_b64_size <= effective_limit:
            logger.info(
                f"Видео не требует сжатия: ~{original_b64_size // 1024}KB base64 "
                f"(потолок ~{effective_limit // 1024}KB)"
            )
            return video_path, original_fps, original_fps

        logger.info(
            f"Видео требует сжатия: ~{original_b64_size // 1024}KB base64 "
            f"(потолок ~{effective_limit // 1024}KB). "
            f"Исходное: {orig_width}x{orig_height} @ {original_fps:.1f}fps, "
            f"{total_frames} кадров"
        )

        # Подбираем параметры сжатия
        params = self._select_compression_params(
            original_fps=original_fps,
            orig_width=orig_width,
            orig_height=orig_height,
            total_frames=total_frames,
            original_b64_size=original_b64_size,
            size_limit=effective_limit,
        )

        compressed_path = self._encode_video(video_path, **params)
        compressed_b64 = self._estimate_b64_size(compressed_path)
        logger.info(
            f"Сжатое видео: ~{compressed_b64 // 1024}KB base64, params={params}"
        )

        orig_max_side = max(orig_width, orig_height)
        iteration = 0
        while compressed_b64 > effective_limit:
            iteration += 1
            overshoot = compressed_b64 / float(effective_limit)
            if overshoot <= 1.02:
                break

            at_minimum = (
                params["target_fps"] <= 1
                and params["jpeg_quality"] <= 22
                and params["max_side"] <= 256
            )
            if at_minimum:
                logger.warning(
                    "Минимум параметров сжатия, файл всё ещё выше потолка — "
                    "останавливаем локальное сжатие (дальше сработает дожим при отправке)"
                )
                break

            old_path = compressed_path
            shrink = min(max(overshoot**0.42, 1.15), 2.85)

            params["target_fps"] = max(1, int(params["target_fps"] / shrink))
            params["jpeg_quality"] = max(
                22, int(params["jpeg_quality"] / (shrink**0.38))
            )
            params["max_side"] = max(256, int(params["max_side"] / (shrink**0.42)))
            if params["max_side"] > orig_max_side:
                params["max_side"] = orig_max_side
            if params["target_fps"] > original_fps:
                params["target_fps"] = max(1, int(original_fps))

            if old_path != video_path:
                os.unlink(old_path)

            compressed_path = self._encode_video(video_path, **params)
            compressed_b64 = self._estimate_b64_size(compressed_path)
            logger.info(
                f"Сжатие #{iteration} (превышение ×{overshoot:.2f}): "
                f"~{compressed_b64 // 1024}KB base64, params={params}"
            )
            if iteration >= 7:
                break

        return compressed_path, original_fps, float(params["target_fps"])

    def _select_compression_params(
        self,
        original_fps: float,
        orig_width: int,
        orig_height: int,
        total_frames: int,
        original_b64_size: int,
        size_limit: int,
    ) -> Dict[str, Any]:
        """Выбирает оптимальные параметры сжатия на основе коэффициента."""
        ratio = original_b64_size / max(1, size_limit)

        # Базовые параметры
        target_fps = COMPRESSED_FPS
        max_side = MAX_FRAME_SIDE
        jpeg_quality = JPEG_QUALITY

        if ratio > 4:
            # Очень большое видео
            target_fps = 1
            max_side = 960
            jpeg_quality = 45
        elif ratio > 2:
            # Большое видео
            target_fps = 1
            max_side = 1280
            jpeg_quality = 55
        elif ratio > 1.5:
            # Умеренно большое
            target_fps = 2
            max_side = 1280
            jpeg_quality = 60
        else:
            # Немного превышает лимит
            target_fps = 2
            max_side = 1920
            jpeg_quality = 70

        # Не увеличиваем разрешение
        orig_max_side = max(orig_width, orig_height)
        if max_side > orig_max_side:
            max_side = orig_max_side

        # Не увеличиваем FPS выше исходного
        if target_fps > original_fps:
            target_fps = max(1, int(original_fps))

        return {
            "target_fps": target_fps,
            "max_side": max_side,
            "jpeg_quality": jpeg_quality,
        }

    def _encode_video(
        self,
        video_path: str,
        target_fps: int,
        max_side: int,
        jpeg_quality: int,
    ) -> str:
        """
        Перекодирует видео с заданными параметрами.
        Использует MJPEG-контейнер через OpenCV (без ffmpeg зависимости).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось открыть видеофайл для перекодирования",
            )

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Вычисляем новое разрешение с сохранением соотношения сторон
        scale = min(max_side / max(orig_width, orig_height, 1), 1.0)
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)
        # Округляем до чётных чисел (требование кодеков)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        new_width = max(new_width, 2)
        new_height = max(new_height, 2)

        # Шаг пропуска кадров
        frame_step = max(1, int(round(src_fps / target_fps)))

        tmp_out = tempfile.NamedTemporaryFile(
            delete=False, suffix=".avi"
        )
        tmp_out.close()

        # MJPEG даёт лучший контроль над размером чем mp4v в OpenCV
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(
            tmp_out.name,
            fourcc,
            float(target_fps),
            (new_width, new_height),
        )

        if not writer.isOpened():
            cap.release()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось создать VideoWriter для сжатия",
            )

        frame_idx = 0
        written = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_step == 0:
                if scale < 1.0:
                    frame = cv2.resize(
                        frame,
                        (new_width, new_height),
                        interpolation=cv2.INTER_AREA,
                    )
                # Применяем JPEG-сжатие к каждому кадру
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
                ok, buf = cv2.imencode(".jpg", frame, encode_params)
                if ok:
                    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                    writer.write(frame)
                    written += 1
            frame_idx += 1

        cap.release()
        writer.release()

        logger.info(
            f"Перекодировано: {written} кадров @ {target_fps}fps, "
            f"{new_width}x{new_height}, качество={jpeg_quality}"
        )

        return tmp_out.name

    def read_as_base64(self, video_path: str) -> Tuple[str, str]:
        """
        Читает файл и возвращает (mime_type, base64_string).
        Определяет mime_type по расширению.
        """
        ext = os.path.splitext(video_path)[1].lower()
        mime_map = {
            ".mp4": "video/mp4",
            ".avi": "video/avi",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
        }
        mime = mime_map.get(ext, "video/mp4")

        with open(video_path, "rb") as f:
            data = f.read()

        b64 = base64.b64encode(data).decode("utf-8")
        logger.info(
            f"Base64 размер для отправки: {len(b64) // 1024}KB "
            f"(лимит {self.MAX_BASE64_BYTES // 1024}KB)"
        )
        return mime, b64


class VideoAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=configs.AI_API_KEY,
            base_url=configs.AI_BASE_URL,
            timeout=httpx.Timeout(300.0, connect=30.0),
            max_retries=2,
        )
        self.model = configs.AI_MODEL
        self.fps = configs.AI_VIDEO_FPS
        self.fps_max = max(1, int(configs.AI_VIDEO_FPS_MAX or 12))
        self.compressor = VideoCompressor(configs.AI_VIDEO_MAX_BASE64_BYTES)

    def _effective_api_fps(self) -> int:
        return max(1, min(int(round(float(self.fps or 1))), self.fps_max))

    async def analyze_video(self, video_file: UploadFile) -> List[VideoStepData]:
        """
        Полный пайплайн:
        1. Сохраняет видео во временный файл
        2. При необходимости — анализ-прокси и сжатие под лимит API
        3. Отправляет в AI-модель для анализа
        4. Парсит ответ (шаги, bbox, типы действий)
        5. Извлекает кадры из ОРИГИНАЛЬНОГО видео по таймкодам
        6. Возвращает список VideoStepData
        """
        # Сохраняем оригинал
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp4"
        ) as tmp:
            tmp.write(await video_file.read())
            original_path = tmp.name

        compressed_path: Optional[str] = None
        proxy_path: Optional[str] = None

        try:
            work_path = original_path
            if configs.AI_VIDEO_ALWAYS_ANALYSIS_PROXY:
                try:
                    proxy_path = self.compressor.build_analysis_proxy(original_path)
                    work_path = proxy_path
                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(
                        f"Не удалось подготовить анализ-прокси, используем исходник: {e}"
                    )

            compressed_path, source_file_fps, delivery_fps = (
                self.compressor.compress_video(work_path)
            )

            send_path = compressed_path
            api_fps = self._effective_api_fps()
            logger.info(
                f"Отправка в AI: прокси={'да' if proxy_path else 'нет'}, "
                f"вход_compress={'прокси' if proxy_path and work_path == proxy_path else 'оригинал'}, "
                f"fps {source_file_fps:.1f}→{delivery_fps:.1f}, api_fps={api_fps}"
            )

            ai_response = self._call_ai_model(
                send_path,
                fps=api_fps,
                max_tokens=6000,
                original_fps=source_file_fps,
                compressed_fps=delivery_fps,
            )
            steps_payload = self._parse_ai_response(ai_response)

            if not steps_payload:
                logger.warning(
                    f"Первичный ответ AI без валидных шагов — fallback. "
                    f"Фрагмент: {repr((ai_response or '')[:800])}"
                )
                ai_response = self._call_ai_model(
                    send_path,
                    prompt=FALLBACK_ANALYSIS_PROMPT,
                    fps=api_fps,
                    max_tokens=6400,
                    original_fps=source_file_fps,
                    compressed_fps=delivery_fps,
                )
                steps_payload = self._parse_ai_response(ai_response)
                if not steps_payload:
                    logger.warning(
                        f"Fallback без шагов, фрагмент: {repr((ai_response or '')[:800])}"
                    )
                    logger.warning(
                        "Запрос repair: компактный JSON шагов (тот же ролик)"
                    )
                    ai_response = self._call_ai_model(
                        send_path,
                        prompt=REPAIR_JSON_PROMPT,
                        fps=api_fps,
                        max_tokens=6000,
                        original_fps=source_file_fps,
                        compressed_fps=delivery_fps,
                    )
                    steps_payload = self._parse_ai_response(ai_response)
                if not steps_payload:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            "AI не вернула пригодный список шагов (JSON/bbox). "
                            "Проверьте логи: фрагмент ответа записан уровнем WARNING."
                        ),
                    )

            is_compressed = compressed_path != original_path
            if is_compressed and delivery_fps != source_file_fps:
                steps_payload = self._remap_timecodes(
                    steps_payload,
                    compressed_fps=delivery_fps,
                    original_fps=source_file_fps,
                    original_path=original_path,
                )

            # Кадры извлекаем из ОРИГИНАЛА для высокого качества
            results = self._extract_frames_at_timecodes(
                original_path, steps_payload
            )
            return results

        finally:
            cleanup_paths = {original_path}
            if proxy_path:
                cleanup_paths.add(proxy_path)
            if compressed_path:
                cleanup_paths.add(compressed_path)
            for p in cleanup_paths:
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    def _remap_timecodes(
        self,
        steps: List[Dict[str, Any]],
        compressed_fps: float,
        original_fps: float,
        original_path: str,
    ) -> List[Dict[str, Any]]:
        """
        Если видео было сжато с другим FPS, таймкоды остаются корректными
        (мы только пропускаем кадры, а не ускоряем видео).
        
        Однако если масштабирование по времени произошло, нужна коррекция.
        В нашем случае frame_step просто пропускает кадры, время не меняется,
        поэтому таймкоды совпадают. Метод оставлен для будущих нужд.
        """
        # Поскольку мы используем frame_step (пропуск кадров без изменения скорости),
        # таймкоды в секундах остаются идентичными оригиналу.
        # Коррекция не требуется.
        logger.debug(
            f"Ремаппинг таймкодов: compressed_fps={compressed_fps}, "
            f"original_fps={original_fps} — пропуск не нужен (frame_step метод)"
        )
        return steps

    def _call_ai_model(
        self,
        video_path: str,
        prompt: Optional[str] = None,
        fps: Optional[int] = None,
        max_tokens: Optional[int] = None,
        original_fps: Optional[float] = None,
        compressed_fps: Optional[float] = None,
    ) -> str:
        """
        Кодирует видео в base64 и отправляет в AI-модель.
        Перед отправкой проверяет размер и при необходимости
        дополнительно сжимает.
        """
        mime, base64_video = self.compressor.read_as_base64(video_path)
        limit = self.compressor.MAX_BASE64_BYTES

        # Финальная проверка — дополнительные ступени перекодирования под потолок API
        if len(base64_video) > limit:
            logger.warning(
                f"Base64 ({len(base64_video) // 1024}KB) выше потолка ({limit // 1024}KB), "
                "пробуем дополнительные профили сжатия."
            )
            emergency_tiers = [
                (1, 640, 35),
                (1, 480, 30),
                (1, 400, 28),
                (1, 320, 25),
                (1, 256, 22),
                (1, 256, 20),
            ]
            for tier_fps, tier_side, tier_q in emergency_tiers:
                emergency_path = self.compressor._encode_video(
                    video_path,
                    target_fps=tier_fps,
                    max_side=tier_side,
                    jpeg_quality=tier_q,
                )
                try:
                    mime, base64_video = self.compressor.read_as_base64(emergency_path)
                    if len(base64_video) <= limit:
                        break
                finally:
                    if os.path.exists(emergency_path):
                        os.unlink(emergency_path)

            if len(base64_video) > limit:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        "Не удалось уложить видео в допустимый размер для AI даже при "
                        "минимальном качестве. Попробуйте более короткий ролик или "
                        "уменьшите разрешение исходной записи."
                    ),
                )

        effective_fps = fps if fps is not None else self._effective_api_fps()

        logger.info(
            f"Отправка в AI: {len(base64_video) // 1024}KB base64, "
            f"api_fps={effective_fps}, model={self.model}"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": f"data:{mime};base64,{base64_video}"
                                },
                                "fps": effective_fps,
                            },
                            {"type": "text", "text": prompt or ANALYSIS_PROMPT},
                        ],
                    }
                ],
                max_tokens=max_tokens if max_tokens is not None else 8000,
                temperature=0.0,
            )
        except Exception as e:
            logger.exception(
                f"Запрос к провайдеру AI для видео завершился ошибкой (model={self.model})"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Провайдер AI не обработал видео. Проверьте API-ключ, квоты и название "
                    f"модели в AI_MODEL. Детали: {str(e)}"
                ),
            ) from e

        content = completion.choices[0].message.content
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Провайдер AI вернул пустой ответ при разборе видео.",
            )
        return content

    @staticmethod
    def _strip_model_noise(text: str) -> str:
        """Убирает типичные обёртки моделей, мешающие json.loads."""
        if not text:
            return ""
        t = text.strip()
        t = re.sub(
            r"<(?:redacted_)?thinking>[\s\S]*?</(?:redacted_)?thinking>",
            "",
            t,
            flags=re.IGNORECASE,
        )
        return t.strip()

    def _parse_ai_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """
        Парсит JSON из ответа AI. Поддерживает:
        - новый формат: {"steps": [...]}
        - устаревший: {"00:00": {"question", "bbox"}}
        """
        text = self._strip_model_noise(raw_response)

        code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if code_block:
            text = code_block.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    return []
            else:
                return []

        if isinstance(data, list):
            return self._validate_steps_list(data)

        if not isinstance(data, dict):
            return []

        if isinstance(data.get("steps"), list):
            return self._validate_steps_list(data["steps"])
        if isinstance(data.get("data"), dict) and isinstance(
            data["data"].get("steps"), list
        ):
            return self._validate_steps_list(data["data"]["steps"])
        if isinstance(data.get("result"), dict) and isinstance(
            data["result"].get("steps"), list
        ):
            return self._validate_steps_list(data["result"]["steps"])
        if isinstance(data.get("actions"), list):
            return self._validate_steps_list(data["actions"])

        return self._legacy_dict_to_steps(data)

    def _coerce_bbox(self, raw: Any) -> Optional[List[float]]:
        """
        Поддержка bbox как:
        - [x1, y1, x2, y2]
        - {"x1","y1","x2","y2"}
        - {"left","top","right","bottom"}
        - {"x","y","width","height"}  -> x2=x+width, y2=y+height
        """
        if isinstance(raw, list) and len(raw) == 4:
            try:
                return [float(v) for v in raw]
            except (TypeError, ValueError):
                return None

        if not isinstance(raw, dict):
            return None

        def _get(*keys):
            for k in keys:
                if k in raw and raw[k] is not None:
                    return raw[k]
            return None

        x1 = _get("x1", "xmin", "left")
        y1 = _get("y1", "ymin", "top")
        x2 = _get("x2", "xmax", "right")
        y2 = _get("y2", "ymax", "bottom")
        if None not in (x1, y1, x2, y2):
            try:
                return [float(x1), float(y1), float(x2), float(y2)]
            except (TypeError, ValueError):
                return None

        x = _get("x")
        y = _get("y")
        w = _get("w", "width")
        h = _get("h", "height")
        if None not in (x, y, w, h):
            try:
                xf, yf, wf, hf = float(x), float(y), float(w), float(h)
                return [xf, yf, xf + wf, yf + hf]
            except (TypeError, ValueError):
                return None
        return None

    def _normalize_bbox_scale(self, bbox: List[float]) -> List[float]:
        """
        Приводит bbox к нормализованному виду 0..1.
        Модель может вернуть:
        - 0..1 (нормализованный)
        - 0..100 (проценты)
        """
        if not bbox or len(bbox) != 4:
            return bbox
        if all(0.0 <= b <= 100.0 for b in bbox) and any(b > 1.0 for b in bbox):
            return [b / 100.0 for b in bbox]
        return bbox

    def _normalize_instruction_md(self, raw: str) -> str:
        s = str(raw or "").strip()
        if not s:
            return ""
        s = s.replace("\\r\\n", "\n").replace("\\n", "\n")
        s = re.sub(r"\s*(##\s+)", r"\n\n\1", s)
        s = re.sub(
            r"(##\s*(?:Цель|Действие|Контекст|Результат|Шаг))\s+", r"\1\n\n", s
        )
        s = re.sub(r"\s-\s", "\n- ", s)
        s = re.sub(r"\n{3,}", "\n\n", s).strip()
        return s

    def _validate_steps_list(self, steps: Any) -> List[Dict[str, Any]]:
        if not isinstance(steps, list):
            return []

        validated: List[Dict[str, Any]] = []
        for item in steps:
            if not isinstance(item, dict):
                continue
            tb = str(item.get("timecode_before", "")).strip()
            ta = str(item.get("timecode_after", "")).strip()
            legacy_tc = str(item.get("timecode", "")).strip()
            timecode_before = tb or legacy_tc
            timecode_after = ta
            timecode = timecode_before
            title = str(item.get("title", "")).strip()
            instruction_md = self._normalize_instruction_md(
                item.get("instruction_md", "")
            )
            inter = item.get("interaction")
            if not isinstance(inter, dict):
                inter = item

            itype = _normalize_interaction_type(
                str(
                    inter.get("type")
                    or inter.get("interaction_type")
                    or "left_click"
                )
            )
            bbox = self._coerce_bbox(inter.get("bbox"))
            expected_text = inter.get("expected_text")
            key_chord = _normalize_key_chord(inter.get("key_chord"))

            if not timecode_before or not isinstance(bbox, list) or len(bbox) != 4:
                logger.warning(
                    "Пропущен шаг: некорректный timecode_before/timecode или bbox"
                )
                continue

            if not instruction_md and not title:
                logger.warning(
                    f"Пропущен шаг {timecode_before}: нет текста задания"
                )
                continue

            try:
                bbox = [float(b) for b in bbox]
            except (ValueError, TypeError):
                continue

            bbox = self._normalize_bbox_scale(bbox)
            x1, y1, x2, y2 = bbox
            bbox = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]

            is_norm = all(0.0 <= b <= 1.0 for b in bbox)
            if is_norm:
                bbox = [max(0.0, min(1.0, b)) for b in bbox]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                if width <= 0 or height <= 0:
                    continue
                if width < 0.005 or height < 0.005:
                    logger.warning(
                        f"Шаг {timecode_before}: bbox очень маленький, пропуск"
                    )
                    continue
                if width > 0.95 or height > 0.95:
                    logger.warning(
                        f"Шаг {timecode_before}: bbox слишком большой, пропуск"
                    )
                    continue
            else:
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                if width < 2.0 or height < 2.0:
                    logger.warning(
                        f"Шаг {timecode_before}: bbox в пикселях слишком мал, пропуск"
                    )
                    continue
                if width > 8192 or height > 8192:
                    logger.warning(
                        f"Шаг {timecode_before}: bbox в пикселях нереалистичен, пропуск"
                    )
                    continue

            if itype == "text_input":
                if expected_text is not None:
                    expected_text = (
                        str(expected_text)
                        .replace("\r\n", "\n")
                        .replace("\r", "\n")
                        .replace("\\n", "\n")
                        .strip()
                        or None
                    )
                if not expected_text:
                    logger.warning(
                        f"Пропущен шаг {timecode_before}: text_input без expected_text"
                    )
                    continue
            else:
                expected_text = None

            if itype != "key_chord":
                key_chord = None

            if not title and instruction_md:
                title = instruction_md.split("\n", 1)[0].strip("# ")[:120]

            validated.append(
                {
                    "timecode": timecode,
                    "timecode_before": timecode_before,
                    "timecode_after": timecode_after or None,
                    "title": title or f"Шаг {len(validated) + 1}",
                    "instruction_md": instruction_md
                    or title
                    or "Выполните действие на экране.",
                    "interaction_type": itype,
                    "bbox": bbox,
                    "expected_text": expected_text,
                    "key_chord": key_chord,
                }
            )

        return validated

    def _legacy_dict_to_steps(self, data: Dict) -> List[Dict[str, Any]]:
        """Старый формат: таймкод -> {question, bbox}."""
        validated: List[Dict[str, Any]] = []
        for timecode, value in data.items():
            if not isinstance(value, dict):
                continue
            question = value.get("question", "")
            bbox = value.get("bbox", [])
            if not question or not isinstance(bbox, list) or len(bbox) != 4:
                continue
            try:
                bbox = [float(b) for b in bbox]
            except (ValueError, TypeError):
                continue
            bbox = [max(0.0, min(1.0, b)) for b in bbox]
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if width <= 0 or height <= 0:
                continue
            if width < 0.01 or height < 0.01:
                continue
            if width > 0.9 or height > 0.9:
                continue
            q = str(question).strip()
            tc = str(timecode).strip()
            validated.append(
                {
                    "timecode": tc,
                    "timecode_before": tc,
                    "timecode_after": None,
                    "title": q[:120] if q else "Шаг",
                    "instruction_md": q,
                    "interaction_type": "left_click",
                    "bbox": bbox,
                    "expected_text": None,
                    "key_chord": None,
                }
            )
        return validated

    def _timecode_to_seconds(self, timecode: str) -> float:
        """Конвертирует ММ:СС(.ms) или ЧЧ:ММ:СС(.ms) в секунды."""
        parts = timecode.strip().split(":")
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            return 0
        except ValueError:
            return 0

    def _frame_to_png_bytes(self, frame: Any) -> Optional[bytes]:
        ok, buf = cv2.imencode(".png", frame)
        return buf.tobytes() if ok else None

    def _read_frame_at_seconds(
        self,
        cap: cv2.VideoCapture,
        target_seconds: float,
        fps: float,
        total_frames: int,
        duration: float,
    ) -> Any:
        """Возвращает BGR-кадр или None."""
        ts = max(0.0, float(target_seconds))
        if duration and ts > duration:
            ts = max(0.0, duration - 0.05)

        frame_number = int(round(ts * fps))
        if total_frames > 0:
            frame_number = max(0, min(frame_number, total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if not ret or frame is None:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ret, frame = cap.read()
        return frame if ret and frame is not None else None

    def _extract_frames_at_timecodes(
        self, video_path: str, steps_payload: List[Dict[str, Any]]
    ) -> List[VideoStepData]:
        """Извлекает кадры «до» и опционально «после» по шагам."""
        frame_lead_sec = max(0.0, float(configs.AI_VIDEO_FRAME_OFFSET_SEC))
        after_lag_sec = max(0.0, float(configs.AI_VIDEO_AFTER_FRAME_LAG_SEC))

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Не удалось открыть видеофайл",
            )

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps else 0

        results: List[VideoStepData] = []

        sorted_steps = sorted(
            steps_payload,
            key=lambda s: self._timecode_to_seconds(s["timecode"]),
        )

        for step in sorted_steps:
            timecode = step["timecode"]
            tc_before = step.get("timecode_before") or timecode
            tc_after = step.get("timecode_after")
            bbox = step["bbox"]

            before_seconds = self._timecode_to_seconds(tc_before)
            target_before = max(0.0, before_seconds - frame_lead_sec)

            frame = self._read_frame_at_seconds(
                cap, target_before, fps, total_frames, duration
            )
            if frame is None:
                logger.warning(
                    f"Не удалось извлечь кадр «до» для таймкода {tc_before}"
                )
                continue

            height, width = frame.shape[:2]
            png_before = self._frame_to_png_bytes(frame)
            if not png_before:
                continue

            after_bytes: Optional[bytes] = None
            if tc_after:
                after_seconds = self._timecode_to_seconds(tc_after) + after_lag_sec
                if after_seconds <= before_seconds:
                    after_seconds = before_seconds + 0.15
                if duration and after_seconds > duration - 0.04:
                    after_seconds = max(target_before, duration - 0.04)
                frame_after = self._read_frame_at_seconds(
                    cap, after_seconds, fps, total_frames, duration
                )
                if frame_after is not None:
                    after_png = self._frame_to_png_bytes(frame_after)
                    if after_png and after_png != png_before:
                        after_bytes = after_png
                    elif after_png == png_before:
                        logger.warning(
                            f"Кадры до/после совпали для шага {tc_before}, "
                            "timecode_after уточните в видео"
                        )

            results.append(
                VideoStepData(
                    timecode=timecode,
                    instruction_md=step["instruction_md"],
                    step_title=step["title"],
                    bbox=bbox,
                    frame_bytes=png_before,
                    frame_width=width,
                    frame_height=height,
                    action_type_key=step["interaction_type"],
                    expected_text=step.get("expected_text"),
                    key_chord=step.get("key_chord"),
                    timecode_before=tc_before,
                    timecode_after=tc_after,
                    after_frame_bytes=after_bytes,
                )
            )

        cap.release()
        return results

    async def rewrite_task_text(self, text: str) -> str:
        prompt = (
            "Улучши следующий текст описания/инструкции шага для интерактивного тренинга. "
            "Сделай его понятным и кратким, исправь опечатки и используй уместную Markdown-разметку. "
            "Можешь добавить немного эмодзи для живости. "
            "Верни ТОЛЬКО улучшенный текст без вступительных фраз вроде "
            "'Конечно, вот улучшенный текст:' и без markdown-блока ```markdown.\n\n"
            f"Исходный текст:\n{text}"
        )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7,
        )

        result = completion.choices[0].message.content.strip()
        for prefix in ("```markdown", "```md", "```"):
            if result.startswith(prefix):
                result = result[len(prefix):]
                break
        if result.endswith("```"):
            result = result[:-3]

        return result.strip()

    def stream_rewrite_task_text(self, text: str):
        prompt = (
            "Улучши следующий текст описания/инструкции шага для интерактивного тренинга. "
            "Сделай его понятным и кратким, исправь опечатки и используй уместную Markdown-разметку. "
            "Можешь добавить немного эмодзи для живости. "
            "Верни ТОЛЬКО улучшенный текст без вступительных фраз вроде "
            "'Конечно, вот улучшенный текст:' и без markdown-блока ```markdown.\n\n"
            f"Исходный текст:\n{text}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta