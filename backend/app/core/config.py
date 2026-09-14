import os
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Notification & Mailing Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    SECRET_KEY: str = "supersecretkeyformailingapplication1234567890abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "sqlite:///./mailing.db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6389/0"
    CELERY_BROKER_URL: str = "redis://localhost:6389/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6389/0"

    # SMTP / Mail Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    SMTP_TLS: bool = False
    SMTP_SSL: bool = False
    EMAILS_FROM_EMAIL: str = "noreply@notifications.local"
    EMAILS_FROM_NAME: str = "Notification Service"

    # Unsubscribe & Links
    UNSUBSCRIBE_BASE_URL: str = "http://localhost:5173/unsubscribe"

    # Initial Superuser
    FIRST_SUPERUSER_EMAIL: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123456"

    # Rate limiting (emails per second per worker)
    SEND_RATE_LIMIT_PER_SEC: int = 20

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
