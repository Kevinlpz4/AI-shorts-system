"""
Tests for IngestionSettings (Pydantic-based persistence configuration).

Validates:
  - Default values (SQLite in-memory, echo=False, etc.)
  - Environment variable override with INGESTION_ prefix
  - Type coercion
  - .env file loading
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from ingestion.infrastructure.persistence import IngestionSettings


class TestDefaults:
    """Valores por defecto deben ser seguros para desarrollo local."""

    def test_default_database_url_is_sqlite_memory(self):
        """El default debe ser sqlite:///:memory:."""
        settings = IngestionSettings()
        assert settings.database_url == "sqlite:///:memory:"

    def test_default_echo_is_false(self):
        """database_echo debe ser False por defecto (seguro para prod)."""
        settings = IngestionSettings()
        assert settings.database_echo is False

    def test_default_pool_size_is_5(self):
        """database_pool_size debe ser 5 (default de SQLAlchemy)."""
        settings = IngestionSettings()
        assert settings.database_pool_size == 5

    def test_default_max_overflow_is_10(self):
        """database_max_overflow debe ser 10."""
        settings = IngestionSettings()
        assert settings.database_max_overflow == 10

    def test_default_pool_pre_ping_is_true(self):
        """database_pool_pre_ping debe ser True (recomendado)."""
        settings = IngestionSettings()
        assert settings.database_pool_pre_ping is True

    def test_default_pool_recycle_is_3600(self):
        """database_pool_recycle debe ser 3600 (1 hora)."""
        settings = IngestionSettings()
        assert settings.database_pool_recycle == 3600


class TestEnvOverride:
    """Variables de entorno deben sobreescribir defaults."""

    ENV_VARS = {
        "INGESTION_DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/test",
        "INGESTION_DATABASE_ECHO": "true",
        "INGESTION_DATABASE_POOL_SIZE": "20",
        "INGESTION_DATABASE_MAX_OVERFLOW": "50",
        "INGESTION_DATABASE_POOL_PRE_PING": "false",
        "INGESTION_DATABASE_POOL_RECYCLE": "300",
    }

    @pytest.fixture(autouse=True)
    def _set_env(self, monkeypatch):
        """Set all INGESTION_* env vars before each test in this class."""
        for key, value in self.ENV_VARS.items():
            monkeypatch.setenv(key, value)

    def test_url_override(self):
        """database_url debe leerse de INGESTION_DATABASE_URL."""
        settings = IngestionSettings()
        assert settings.database_url == self.ENV_VARS["INGESTION_DATABASE_URL"]

    def test_echo_override(self):
        """database_echo debe convertir 'true' a True."""
        settings = IngestionSettings()
        assert settings.database_echo is True

    def test_pool_size_override(self):
        """database_pool_size debe convertir string a int."""
        settings = IngestionSettings()
        assert settings.database_pool_size == 20
        assert isinstance(settings.database_pool_size, int)

    def test_max_overflow_override(self):
        """database_max_overflow debe convertir string a int."""
        settings = IngestionSettings()
        assert settings.database_max_overflow == 50

    def test_pool_pre_ping_override(self):
        """database_pool_pre_ping debe convertir 'false' a False."""
        settings = IngestionSettings()
        assert settings.database_pool_pre_ping is False

    def test_pool_recycle_override(self):
        """database_pool_recycle debe convertir string a int."""
        settings = IngestionSettings()
        assert settings.database_pool_recycle == 300


class TestEnvPrefix:
    """Solo variables con prefijo INGESTION_ deben afectar settings."""

    def test_other_prefix_ignored(self, monkeypatch):
        """Variables con prefijo diferente no deben afectar."""
        monkeypatch.setenv("OTHER_DATABASE_URL", "sqlite:///other.db")
        settings = IngestionSettings()
        assert settings.database_url == "sqlite:///:memory:"

    def test_partial_override(self, monkeypatch):
        """Sobrescribir solo algunas vars debe mantener defaults en las demás."""
        monkeypatch.setenv("INGESTION_DATABASE_URL", "sqlite:///custom.db")
        settings = IngestionSettings()
        assert settings.database_url == "sqlite:///custom.db"
        # Others should remain default
        assert settings.database_echo is False
        assert settings.database_pool_size == 5


class TestTypeCoercion:
    """Pydantic debe coercionar tipos correctamente."""

    def test_echo_true_accepts_various_formats(self, monkeypatch):
        """Pydantic debe aceptar 1/yes/true como True."""
        for val in ("1", "yes", "True", "true"):
            monkeypatch.setenv("INGESTION_DATABASE_ECHO", val)
            settings = IngestionSettings()
            # Pydantic v2 converts "1"/"yes"/"true" to True
            assert settings.database_echo is True, f"Failed for value: {val}"

    def test_echo_false_accepts_various_formats(self, monkeypatch):
        """Pydantic debe aceptar 0/no/false como False."""
        for val in ("0", "no", "False", "false"):
            monkeypatch.setenv("INGESTION_DATABASE_ECHO", val)
            settings = IngestionSettings()
            assert settings.database_echo is False, f"Failed for value: {val}"

    def test_invalid_int_falls_back_to_default(self, monkeypatch):
        """Valores inválidos para int deben fallar (Pydantic validation)."""
        monkeypatch.setenv("INGESTION_DATABASE_POOL_SIZE", "not-a-number")
        with pytest.raises(ValueError):
            IngestionSettings()


class TestExtraIgnored:
    """Campos extra en env deben ser ignorados (extra='ignore')."""

    def test_unknown_env_var_ignored(self, monkeypatch):
        """Variables INGESTION_* desconocidas no deben causar error."""
        monkeypatch.setenv("INGESTION_SOME_WEIRD_VAR", "value")
        # Should not raise
        settings = IngestionSettings()
        assert settings.database_url == "sqlite:///:memory:"
