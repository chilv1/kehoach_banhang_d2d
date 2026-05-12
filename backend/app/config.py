"""Cấu hình ứng dụng."""
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ProjectWeb — MS Project clone"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'projectweb.db'}"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    DEFAULT_WORK_HOURS_PER_DAY: float = 8.0
    DEFAULT_WORK_DAYS_PER_WEEK: int = 5


settings = Settings()
