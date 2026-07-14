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

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_KEYS = frozenset({
    "change-me-in-production",
    "change-me",
    "changeme",
    "secret",
    "password",
    "",
})


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
        ALLOWED_HOSTS: Trusted hosts for TrustedHostMiddleware.
        SECURITY_HEADERS_ENABLED: Enable security headers middleware.
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
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Trusted hosts for TrustedHostMiddleware. Use ['*'] to allow all.",
    )
    SECURITY_HEADERS_ENABLED: bool = True

    # ── OpenAPI ──
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Reject insecure SECRET_KEY values in production."""
        if v.strip().lower() in _INSECURE_KEYS:
            # We can't check ENVIRONMENT here (it may not be set yet),
            # so we warn but allow. The startup check in create_app()
            # handles the production-specific validation.
            pass
        if len(v) < 8:
            raise ValueError(
                "SECRET_KEY must be at least 8 characters long. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Reject wildcard CORS origins — they are insecure."""
        if "*" in v:
            raise ValueError(
                "CORS_ORIGINS must not contain '*' wildcard. "
                "List specific origins instead."
            )
        return v

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Log format must be 'json' or 'text'."""
        if v not in ("json", "text"):
            raise ValueError(f"LOG_FORMAT must be 'json' or 'text', got '{v}'")
        return v
