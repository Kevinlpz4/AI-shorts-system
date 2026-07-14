"""
Tests for Dependency Injection Providers (REQ-F3).

Validates:
- get_settings returns a Settings instance from app.state
- get_session_factory returns a sessionmaker from app.state
- get_uow yields a SQLAlchemyUnitOfWork and auto-closes on exit

These are unit tests of the provider functions, not integration tests.
They mock the Request object to test DI wiring in isolation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import sessionmaker as sa_sessionmaker

from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import (
    get_session_factory,
    get_settings,
    get_uow,
)
from ingestion.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


# ── Helpers ──


class _MockApp:
    """Minimal mock of FastAPI app for DI testing."""

    def __init__(self, state=None):
        self.state = state or MagicMock()


class _MockRequest:
    """Minimal mock of FastAPI Request for DI testing."""

    def __init__(self, app=None):
        self.app = app or _MockApp()


# ── Tests ──


class TestGetSettings:
    """Test get_settings dependency provider."""

    def test_get_settings_returns_settings(self):
        """get_settings should return the Settings instance from app.state."""
        settings = Settings(
            ENVIRONMENT="testing",
            DEBUG=False,
            HOST="127.0.0.1",
            PORT=8000,
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=["http://localhost:3000"],
            LOG_LEVEL="INFO",
            LOG_FORMAT="text",
            SECRET_KEY="test-secret-key",
        )
        app = _MockApp(state=MagicMock(settings=settings))
        request = _MockRequest(app=app)

        result = get_settings(request)

        assert isinstance(result, Settings)
        assert result is settings


class TestGetSessionFactory:
    """Test get_session_factory dependency provider."""

    def test_get_session_factory_returns_sessionmaker(self):
        """get_session_factory should return the sessionmaker from app.state."""
        mock_sf = MagicMock(spec=sa_sessionmaker)
        app = _MockApp(state=MagicMock(session_factory=mock_sf))
        request = _MockRequest(app=app)

        result = get_session_factory(request)

        assert result is mock_sf


class TestGetUoW:
    """Test get_uow dependency generator."""

    def test_uow_lifecycle(self):
        """get_uow should yield a SQLAlchemyUnitOfWork and auto-close.

        get_uow is a generator function (FastAPI uses yield-based DI).
        We drive it manually: next() to get the yielded UoW, then
        generator.close() to simulate FastAPI teardown (which calls
        GeneratorExit → triggers the with block's __exit__).
        """
        mock_sf = MagicMock()
        mock_ep = MagicMock()

        with patch(
            "ingestion.presentation.dependencies.SQLAlchemyUnitOfWork"
        ) as MockUoW:
            mock_uow = MagicMock(spec=SQLAlchemyUnitOfWork)
            MockUoW.return_value = mock_uow

            # Drive the generator
            gen = get_uow(
                session_factory=mock_sf,
                event_publisher=mock_ep,
            )

            # First next() runs setup and yields the UoW
            uow = next(gen)
            assert uow is mock_uow
            MockUoW.assert_called_once_with(
                session_factory=mock_sf,
                event_publisher=mock_ep,
            )

            # Simulate FastAPI teardown by closing the generator
            # This triggers GeneratorExit inside the `with uow:` block,
            # which causes __exit__ to be called for cleanup.
            gen.close()
            # If close() raises, the generator didn't clean up properly
            mock_uow.__exit__.assert_called()
