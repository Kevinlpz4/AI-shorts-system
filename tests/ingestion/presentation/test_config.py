"""
Tests for Presentation Configuration (Settings).

Validates:
- Env prefix (AI_SHORTS_) works correctly
- Default values apply when env vars are missing
- Pattern validation rejects invalid ENVIRONMENT values
"""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError


class TestSettingsDefaults:
    """Test Settings default values."""

    def test_settings_creates_with_defaults(self):
        """Settings() should create successfully with default values."""
        from ingestion.presentation.config import Settings

        # Temporarily clear AI_SHORTS_ env vars to ensure defaults
        env_backup = {}
        for key in list(os.environ):
            if key.startswith("AI_SHORTS_"):
                env_backup[key] = os.environ.pop(key)

        try:
            settings = Settings()
            assert settings.ENVIRONMENT == "development"
            assert settings.DEBUG is False
            assert settings.HOST == "0.0.0.0"
            assert settings.PORT == 8000
            assert settings.DATABASE_URL == "sqlite:///./ai_shorts.db"
            assert settings.CORS_ORIGINS == ["http://localhost:3000"]
            assert settings.LOG_LEVEL == "INFO"
            assert settings.LOG_FORMAT == "json"
            assert settings.SECRET_KEY == "change-me-in-production"
            assert settings.app_name == "AI Shorts System"
            assert settings.openapi_version == "1.0.0"
        finally:
            os.environ.update(env_backup)

    def test_docs_urls_default(self):
        """Default docs URLs should be /docs, /redoc, /openapi.json."""
        from ingestion.presentation.config import Settings

        env_backup = {}
        for key in list(os.environ):
            if key.startswith("AI_SHORTS_"):
                env_backup[key] = os.environ.pop(key)

        try:
            settings = Settings()
            assert settings.docs_url == "/docs"
            assert settings.redoc_url == "/redoc"
            assert settings.openapi_url == "/openapi.json"
        finally:
            os.environ.update(env_backup)


class TestSettingsEnvironment:
    """Test Settings from environment variables."""

    def test_env_prefix_works(self, monkeypatch):
        """AI_SHORTS_DATABASE_URL env var should override default."""
        from ingestion.presentation.config import Settings

        monkeypatch.setenv("AI_SHORTS_DATABASE_URL", "postgresql://test:test@localhost/test")
        settings = Settings()
        assert settings.DATABASE_URL == "postgresql://test:test@localhost/test"

    def test_debug_from_env(self, monkeypatch):
        """AI_SHORTS_DEBUG env var should set DEBUG."""
        from ingestion.presentation.config import Settings

        monkeypatch.setenv("AI_SHORTS_DEBUG", "true")
        settings = Settings()
        assert settings.DEBUG is True

    def test_port_from_env(self, monkeypatch):
        """AI_SHORTS_PORT env var should set PORT."""
        from ingestion.presentation.config import Settings

        monkeypatch.setenv("AI_SHORTS_PORT", "9000")
        settings = Settings()
        assert settings.PORT == 9000

    def test_cors_from_env(self, monkeypatch):
        """AI_SHORTS_CORS_ORIGINS should be parsed as list."""
        from ingestion.presentation.config import Settings

        monkeypatch.setenv("AI_SHORTS_CORS_ORIGINS", '["http://localhost:3000","http://localhost:8080"]')
        settings = Settings()
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS


class TestSettingsValidation:
    """Test Settings validation rules."""

    def test_valid_environments_accepted(self):
        """Valid ENVIRONMENT values should be accepted."""
        from ingestion.presentation.config import Settings

        for env in ("development", "testing", "production"):
            env_backup = {}
            for key in list(os.environ):
                if key.startswith("AI_SHORTS_"):
                    env_backup[key] = os.environ.pop(key)
            try:
                settings = Settings(ENVIRONMENT=env)
                assert settings.ENVIRONMENT == env
            finally:
                os.environ.update(env_backup)

    def test_invalid_environment_rejected(self):
        """Invalid ENVIRONMENT values should raise ValidationError."""
        from ingestion.presentation.config import Settings

        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="staging")

    def test_custom_settings_values(self):
        """Settings should accept custom values."""
        from ingestion.presentation.config import Settings

        settings = Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            HOST="127.0.0.1",
            PORT=3000,
            DATABASE_URL="postgresql://prod:pass@db/prod",
            LOG_LEVEL="WARNING",
            LOG_FORMAT="text",
            SECRET_KEY="super-secret",
        )
        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is True
        assert settings.PORT == 3000
        assert settings.SECRET_KEY == "super-secret"
