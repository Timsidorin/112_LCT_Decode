import re
import traceback
import uuid

import httpx
from fastapi import HTTPException

from core.config import configs
from core.logging_config import logger


class GigaChatTTSService:
    def __init__(self):
        self.auth_data = configs.SALUT_SPEECH_AUTORIZATION
        self.client_id = configs.CLIENT_ID_SALUTESPEECH

    async def get_access_token(self) -> str:
        if not self.auth_data or self.auth_data in ("your-base64-auth-here", ""):
            raise HTTPException(
                status_code=500, detail="Ключ авторизации SaluteSpeech не настроен"
            )

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {self.auth_data}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # Scope: SALUTE_SPEECH_PERS — для физ.лиц, SALUTE_SPEECH_CORP — для юрлиц
        data = {"scope": "SALUTE_SPEECH_PERS"}

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    url, headers=headers, data=data, timeout=15.0
                )
                logger.info(f"[TTS] OAuth ответ: {response.status_code}")
                if response.status_code != 200:
                    logger.error(f"[TTS] OAuth ошибка: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Ошибка авторизации SaluteSpeech: HTTP {response.status_code} — {response.text}",
                    )
                return response.json().get("access_token")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    f"[TTS] Ошибка получения токена: {e}\n{traceback.format_exc()}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка авторизации в SaluteSpeech: {str(e)}",
                )

    def _text_to_ssml(self, html_text: str) -> str:
        """Конвертирует HTML/Markdown текст в SSML с паузами"""
        if not html_text:
            return "<speak></speak>"

        # Заменяем блочные HTML-теги на переносы строк
        text = re.sub(
            r"</?(h[1-6]|p|div|li|br)[^>]*>", "\n", html_text, flags=re.IGNORECASE
        )
        # Убираем оставшиеся HTML-теги
        text = re.sub(r"<[^>]+>", "", text)
        # Декодируем HTML-сущности вручную
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "и")
            .replace("&lt;", "меньше")
            .replace("&gt;", "больше")
            .replace("&quot;", '"')
        )
        # Убираем символы Markdown
        text = text.replace("**", "").replace("*", "").replace("`", "").replace("#", "")
        # Убираем эмодзи (некорректно озвучиваются)
        text = re.sub(r"[\U00010000-\U0010ffff]", "", text, flags=re.UNICODE)
        text = re.sub(r"[\U0001F300-\U0001F9FF]", "", text)

        # Разбиваем на абзацы / пункты списка
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        ssml_parts = []
        for line in lines:
            if not line:
                continue

            # Для улучшения прочтения аббревиатур или технических слов диктором
            # мы можем использовать возможности голоса. Женский голос 'Nec_24000'
            # справляется с ударениями значительно лучше мужских.

            # Возвращаем теги предложений
            ssml_parts.append(f"<s>{line}</s>")

        # Собираем SSML: длинная пауза между логическими блоками
        inner = '<break time="600ms"/>'.join(ssml_parts)

        # Возвращаем паузы после знаков препинания (как было раньше) для выразительности
        inner = re.sub(r"([,;:])\s+", r'\1<break time="200ms"/> ', inner)

        return f"<speak>{inner}</speak>"

    async def synthesize(self, text: str) -> bytes:
        if not text:
            raise ValueError("Пустой текст для синтеза")

        token = await self.get_access_token()
        ssml = self._text_to_ssml(text)
        logger.info(f"[TTS] Синтезируем SSML ({len(ssml)} символов): {ssml[:120]}...")

        url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml",
        }

        # Используем женский голос `Nec_24000` (Наташа).
        # В SberSpeech этот голос обладает одной из лучших систем автоматической
        # расстановки ударений, и он звучит очень выразительно.
        params = {
            "format": "wav16",
            "voice": "Nec_24000",
        }

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    params=params,
                    content=ssml.encode("utf-8"),
                    timeout=60.0,
                )
                logger.info(
                    f"[TTS] Синтез ответ: {response.status_code}, bytes={len(response.content)}"
                )
                if response.status_code != 200:
                    logger.error(f"[TTS] Синтез ошибка: {response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Ошибка SaluteSpeech TTS: HTTP {response.status_code} — {response.text}",
                    )
                return response.content
            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    f"[TTS] Неожиданная ошибка синтеза: {e}\n{traceback.format_exc()}"
                )
                raise HTTPException(
                    status_code=500, detail=f"Ошибка синтеза речи: {str(e)}"
                )
