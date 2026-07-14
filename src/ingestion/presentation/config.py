"""
Presentation Configuration — pydantic-settings based.

Uses ``AI_SHORTS_`` environment prefix for all settings. Validates at
import time (fail-fast) via pydantic's ``ValidationError``.

Usage::

    from ingestion.presentation.config import Settings

    settings = Settings()  # reads from env vars / .env
    print(settings.DATABASE_URL)
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the Presentation Layer.

    All fields are populated from environment variables with the
    ``AI_SHORTS_`` prefix. Example: ``AI_SHORTS_DEBUG=true``.

    Attributes:
        ENVIRONMENT: Runtime environment (development|testing|production).
        DEBUG: Enable debug mode (SQL echo, verbose errors).
        HOST: Server bind address.
        PORT: Server port.
        DATABASE_URL: SQLAlchemy database URL.
        CORS_ORIGINS: Allowed CORS origins.
        LOG_LEVEL: Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        LOG_FORMAT: Log output format ("json" or "text").
        SECRET_KEY: Application secret key.
        app_name: Application display name.
        openapi_version: API version string.
        docs_url: Swagger UI URL.
        redoc_url: ReDoc URL.
        openapi_url: OpenAPI spec URL.
    """

    model_config = SettingsConfigDict(
        env_prefix="AI_SHORTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──
    app_name: str = "AI Shorts System"
    openapi_version: str = "1.0.0"
    ENVIRONMENT: str = Field(
        default="development",
        pattern="^(development|testing|production)$",
    )
    DEBUG: bool = False

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──
    DATABASE_URL: str = "sqlite:///./ai_shorts.db"

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Logging ──
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"

    # ── Security ──
    SECRET_KEY: str = "change-me-in-production"

    # ── OpenAPI ──
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
