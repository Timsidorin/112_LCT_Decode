import os
from typing import Optional

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configs(BaseSettings):
    """Главный конфиг проекта"""

    # ------------ Настройки проекта ------------
    PROJECT_NAME: str = "Конструктор Тренингов"
    PROJECT_DESCRIPTION: str = (
        "Учебный симулятор подготовки диспетчеров экстренных служб города по вызовам от системы 112. \nТестовый пользователь: test@example.com string"
    )

    # ------------ Веб-сервер ------------
    HOST: str = Field(default="localhost", env="HOST")
    SERVER_HOST: str = Field(default="", env="SERVER_HOST")
    PORT: int = 8004

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

    # ------------ S3 хранилище ----------------------------------------
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default="AWS_ACCESS_KEY_ID", env="AWS_ACCESS_KEY_ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default="AWS_SECRET_ACCESS_KEY", env="AWS_SECRET_ACCESS_KEY"
    )
    S3_BUCKET_NAME: Optional[str] = Field(
        default="S3_BUCKET_NAME", env="S3_BUCKET_NAME"
    )
    S3_ENDPOINT_URL: Optional[str] = Field(
        default="S3_ENDPOINT_URL", env="S3_ENDPOINT_URL"
    )
    S3_REGION_NAME: Optional[str] = Field(default="ru-1", env="S3_REGION_NAME")

    # ------------------- AI Video Analysis ---------------------------------
    AI_API_KEY: Optional[str] = Field(default="AI_API_KEY", env="AI_API_KEY")
    AI_BASE_URL: Optional[str] = Field(
        default="https://routerai.ru/api/v1", env="AI_BASE_URL"
    )

    AI_MODEL: Optional[str] = Field(
        default="qwen/qwen3-vl-30b-a3b-instruct", env="AI_MODEL"
    )
    AI_VIDEO_FPS: int = Field(default=4, env="AI_VIDEO_FPS")

    AI_VIDEO_FPS_MAX: int = Field(default=12, env="AI_VIDEO_FPS_MAX")
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
    AI_VIDEO_MAX_BASE64_BYTES: int = Field(
        default=250_000_000, env="AI_VIDEO_MAX_BASE64_BYTES"
    )
    AI_VIDEO_SOFT_BASE64_BYTES: int = Field(
        default=22_000_000, env="AI_VIDEO_SOFT_BASE64_BYTES"
    )

    AI_VIDEO_FRAME_OFFSET_SEC: float = Field(
        default=0.10, env="AI_VIDEO_FRAME_OFFSET_SEC"
    )
    AI_VIDEO_AFTER_FRAME_LAG_SEC: float = Field(
        default=0.12, env="AI_VIDEO_AFTER_FRAME_LAG_SEC"
    )

    # ------------------- AI Voice (SaluteSpeech) ---------------------------
    CLIENT_ID_SALUTESPEECH: str = Field(default="", env="CLIENT_ID_SALUTESPEECH")
    SALUT_SPEECH_AUTORIZATION: str = Field(default="", env="SALUT_SPEECH_AUTORIZATION")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0", env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND"
    )
    YANDEX_CLIENT_ID: str = Field(default="", env="YANDEX_CLIENT_ID")
    YANDEX_CLIENT_SECRET: str = Field(
        default="",
        validation_alias=AliasChoices("YANDEX_CLIENT_SECRET", "CLIENT_SECRET"),
    )
    YANDEX_REDIRECT_URI: str = Field(
        default="http://localhost:8002/auth/yandex/callback",
        env="YANDEX_REDIRECT_URI",
    )
    FRONTEND_PUBLIC_URL: str = Field(
        default="http://localhost:5173",
        env="FRONTEND_PUBLIC_URL",
    )

    @model_validator(mode="after")
    def _yandex_redirect_non_empty(self) -> "Configs":
        if not (self.YANDEX_REDIRECT_URI or "").strip():
            self.YANDEX_REDIRECT_URI = "http://localhost:8002/auth/yandex/callback"
        return self

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        extra="ignore",
    )


configs = Configs()


def get_db_url():
    return (
        f"postgresql+asyncpg://{configs.DB_USER}:{configs.DB_PASS}@"
        f"{configs.DB_HOST}:{configs.DB_PORT}/{configs.DB_NAME}"
    )


def get_auth_data():
    return {"secret_key": configs.SECRET_KEY, "algorithm": configs.ALGORITHM}
