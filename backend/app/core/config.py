import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "VOGUE FIT - Fashion E-Commerce"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # Security & JWT
    SECRET_KEY: str = "fashion-ecommerce-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database (Read from .env or environment variables in Vercel)
    DATABASE_URL: str = "sqlite:///./fashion_store.db"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 3306
    DB_NAME: Optional[str] = "defaultdb"
    DB_SSL_MODE: Optional[str] = "REQUIRED"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
