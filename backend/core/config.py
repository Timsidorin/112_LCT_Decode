import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configs(BaseSettings):
    """Главный конфиг проекта"""

    # ------------ Настройки проекта ------------
    PROJECT_NAME: str = "Конструктор Тренингов"
    PROJECT_DESCRIPTION: str = (
        "веб-сервис Конструктор тренингов. \nТестовый пользователь: test@example.com string"
    )

    # ------------ Веб-сервер ------------
    HOST: str = Field(default="localhost", env="HOST")
    SERVER_HOST: str = Field(default="", env="SERVER_HOST")
    PORT: int = 8003

    # ------------ Логирование ------------
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # ------------ Аутентификация ------------
    SECRET_KEY: str = Field(
        default="your-secret-key", env="SECRET_KEY"
    )  # Секретный ключ для JWT и шифрования
    ALGORITHM: str = Field(
        default="HS256", env="ALGORITHM"
    )  # Алгоритм шифрования для JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=600000, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )  # Время жизни токена

    # ------------ БД ------------
    DB_HOST: Optional[str] = Field(default="localhost", env="DB_HOST")
    DB_PORT: Optional[int] = Field(default=5432, env="DB_PORT")
    DB_USER: Optional[str] = Field(default="postgres", env="DB_USER")
    DB_NAME: Optional[str] = Field(default="postgres", env="DB_NAME")
    DB_PASS: Optional[str] = Field(default="admin", env="DB_PASS")

    # ------------ Почта (оповещение) ------------
    MAIL_USERNAME: Optional[str] = Field(
        default="timsidorin@gmail.com", env="MAIL_USERNAME"
    )
    MAIL_PASSWORD: Optional[str] = Field(
        default="xdfj qlia vmpy gskl", env="MAIL_PASSWORD"
    )
    MAIL_FROM: Optional[str] = Field(default="timsidorin@gmail.com", env="MAIL_FROM")
    MAIL_PORT: Optional[int] = Field(default=587, env="MAIL_PORT")
    MAIL_SERVER: Optional[str] = Field(default="smtp.gmail.com", env="MAIL_SERVER")
    MAIL_STARTTLS: bool = Field(default=True, env="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(default=False, env="MAIL_SSL_TLS")

    # Настройки OAUTH2

    # ------------ S3 хранилище ----------------------------------------
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default="PBZ2LEBQ3L0Q9PE7N7YY", env="AWS_ACCESS_KEY_ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default="QAjuuUc2Xwwq7rggsNnvXNcnywwXWQ3tNSRS1FNi", env="AWS_SECRET_ACCESS_KEY"
    )
    S3_BUCKET_NAME: Optional[str] = Field(
        default="ec4f5e2a-70163ded-082f-4975-95f1-f0b1bf534bf0", env="S3_BUCKET_NAME"
    )
    S3_ENDPOINT_URL: Optional[str] = Field(
        default="https://s3.twcstorage.ru", env="S3_ENDPOINT_URL"
    )
    S3_REGION_NAME: Optional[str] = Field(default="ru-1", env="S3_REGION_NAME")

    # ------------------- AI Video Analysis ---------------------------------
    AI_API_KEY: Optional[str] = Field(
        default="sk-pLUS5g_b85ENrNiwQnG0Pw", env="AI_API_KEY"
    )
    AI_BASE_URL: Optional[str] = Field(
        default="https://api.vsellm.ru/v1", env="AI_BASE_URL"
    )
    # Instruct без «thinking»: быстрее и предсказуемее JSON для шагов (см. каталог VseLLM).
    AI_MODEL: Optional[str] = Field(
        default="qwen/qwen3-vl-30b-a3b-instruct", env="AI_MODEL"
    )
    # Сколько кадров в секунду «видит» VL-модель при разборе (больше — точнее быстрые клики, тяжелее запрос).
    AI_VIDEO_FPS: int = Field(default=8, env="AI_VIDEO_FPS")

    AI_VIDEO_FPS_MAX: int = Field(default=12, env="AI_VIDEO_FPS_MAX")

    # Перед отправкой в AI всегда собирать облегчённое видео (разрешение + разрежение кадров).
    # Иначе в модель уходит полный исходник (десятки MB base64) — долго и хуже стабильность разбора UI.
    AI_VIDEO_ALWAYS_ANALYSIS_PROXY: bool = Field(
        default=True, env="AI_VIDEO_ALWAYS_ANALYSIS_PROXY"
    )
    AI_VIDEO_ANALYSIS_MAX_SIDE: int = Field(
        default=960, env="AI_VIDEO_ANALYSIS_MAX_SIDE"
    )
    AI_VIDEO_ANALYSIS_ENCODE_FPS: int = Field(
        default=6, env="AI_VIDEO_ANALYSIS_ENCODE_FPS"
    )
    AI_VIDEO_ANALYSIS_JPEG_QUALITY: int = Field(
        default=54, env="AI_VIDEO_ANALYSIS_JPEG_QUALITY"
    )

    # Потолок размера base64 при отправке видео в AI (байты строки base64).
    # Большие исходные файлы сжимаются в VideoCompressor; лимит нужен как страховка для API.
    AI_VIDEO_MAX_BASE64_BYTES: int = Field(
        default=250_000_000, env="AI_VIDEO_MAX_BASE64_BYTES"
    )
    # Целевой потолок до отправки в VL (меньше — быстрее и меньше 5xx у провайдера).
    # Сжатие дожимает прокси, пока оценка base64 не станет не выше этого значения (и не выше MAX).
    AI_VIDEO_SOFT_BASE64_BYTES: int = Field(
        default=22_000_000, env="AI_VIDEO_SOFT_BASE64_BYTES"
    )

    AI_VIDEO_FRAME_OFFSET_SEC: float = Field(
        default=0.10, env="AI_VIDEO_FRAME_OFFSET_SEC"
    )
    # Сдвиг вперёд при извлечении кадра «после» (анимации/переходы UI успели завершиться).
    AI_VIDEO_AFTER_FRAME_LAG_SEC: float = Field(
        default=0.12, env="AI_VIDEO_AFTER_FRAME_LAG_SEC"
    )

    # ------------------- AI Voice (SaluteSpeech) ---------------------------
    CLIENT_ID_SALUTESPEECH: str = Field(
        default="", env="CLIENT_ID_SALUTESPEECH"
    )
    SALUT_SPEECH_AUTORIZATION: str = Field(
        default="", env="SALUT_SPEECH_AUTORIZATION"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )


configs = Configs()


def get_db_url():
    return (
        f"postgresql+asyncpg://{configs.DB_USER}:{configs.DB_PASS}@"
        f"{configs.DB_HOST}:{configs.DB_PORT}/{configs.DB_NAME}"
    )


def get_auth_data():
    return {"secret_key": configs.SECRET_KEY, "algorithm": configs.ALGORITHM}
