"""
Application configuration loaded from environment variables.

All secrets and tunables live in the root .env file.
Pydantic Settings validates them at startup — a missing key fails fast.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# Supported language codes for the platform
LanguageCode = Literal["en", "hi", "kn", "te", "ta"]

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "te": "తెలుగు (Telugu)",
    "ta": "தமிழ் (Tamil)",
}

# Mapping from our language codes to Serper's `hl` parameter
LANGUAGE_TO_SERPER_HL: dict[str, str] = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
    "te": "te",
    "ta": "ta",
}


class Settings(BaseSettings):
    """
    Central configuration.

    To switch from SQLite (dev) to PostgreSQL (prod), change only DATABASE_URL:
      SQLite  → sqlite+aiosqlite:///./smartsiksha.db
      Postgres→ postgresql+asyncpg://user:pass@host:5432/smartsiksha
    """

    model_config = SettingsConfigDict(
        env_file="../.env",       # monorepo root
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- AI / Search ---
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    SERPER_API_KEY: str

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./smartsiksha.db"

    # --- Firebase / Auth ---
    FIREBASE_PROJECT_ID: str = "smart-shiksha"
    JWT_SECRET_KEY: str  # No default — must be set in .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60   # 1 hour

    # --- Unsplash ---
    UNSPLASH_ACCESS_KEY: str = ""

    # --- App ---
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ]

    # --- Rate limits ---
    RATE_LIMIT_ASK: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "30/minute"


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance (cached after first call)."""
    return Settings()
