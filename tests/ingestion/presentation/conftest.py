"""
Test Fixtures for Presentation Layer tests.

Provides shared fixtures for testing the FastAPI Presentation Layer:
- ``app``: Fresh FastAPI application via ``create_app()``
- ``client``: Async httpx client for the app
- ``settings``: Default test Settings
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path for ingestion imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


@pytest.fixture
def settings():
    """Default test settings.

    Uses SQLite in-memory for database and text logging format.
    """
    from ingestion.presentation.config import Settings

    return Settings(
        ENVIRONMENT="testing",
        DEBUG=False,
        HOST="127.0.0.1",
        PORT=8000,
        DATABASE_URL="sqlite:///:memory:",
        CORS_ORIGINS=["http://localhost:3000"],
        LOG_LEVEL="INFO",
        LOG_FORMAT="text",
        SECRET_KEY="test-secret-key",
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
    )


@pytest.fixture
def app(settings):
    """Fresh FastAPI application for each test.

    Creates the app with test settings. Does NOT start a server.
    """
    from ingestion.presentation.app import create_app

    return create_app(settings=settings)


@pytest.fixture
def client(app):
    """Async httpx client for the test app.

    Uses httpx.AsyncClient with the app's ASGI transport.
    """
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def sync_client(app):
    """Sync httpx client for the test app.

    Uses httpx.Client with the app's ASGI transport.
    """
    from httpx import ASGITransport, Client

    transport = ASGITransport(app=app)
    return Client(transport=transport, base_url="http://testserver")
