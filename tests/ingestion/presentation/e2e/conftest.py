"""
Shared fixtures for E2E tests with real infrastructure.

Provides:
- ``e2e_settings``: test Settings with SQLite :memory:
- ``e2e_engine``: real SQLAlchemy engine with StaticPool, tables created
- ``e2e_session_factory``: real sessionmaker bound to engine
- ``e2e_app``: FastAPI app with real DI (overrides get_uow for PerfUnitOfWork)
- ``e2e_client``: httpx AsyncClient wired to the app

Uses PerfUnitOfWork with idempotent ``__enter__`` to handle the double-enter
pattern (get_uow enters UoW, then service enters again via ``with self._uow:``)
which causes transaction isolation issues with SQLite StaticPool.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Self

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ingestion.presentation.config import Settings

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import models to register them in the metadata before create_all
import ingestion.infrastructure.persistence.models  # noqa: F401
from ingestion.infrastructure.persistence.base import PersistenceBase as Base
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


# ============================================================================
# PerfUnitOfWork — idempotent __enter__ for StaticPool safety
# ============================================================================


class PerfUnitOfWork(SQLAlchemyUnitOfWork):
    """UoW subclass with idempotent __enter__/__exit__ for SQLite StaticPool.

    The standard UoW creates a new session on every __enter__ call. With
    StaticPool, two sessions on the same connection cause transaction
    isolation issues — data written by one session is invisible to the other.

    PerfUnitOfWork prevents this by:
    - ``__enter__``: returning self if already entered (no new session)
    - ``__exit__``: only closing when the outermost context exits

    This is TEST-ONLY infrastructure. Production UoW does not need this
    because PostgreSQL connection pools give each session its own connection.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        event_publisher=None,
    ) -> None:
        super().__init__(session_factory, event_publisher)
        self._entered_count = 0

    def __enter__(self) -> Self:
        """Idempotent — only creates session on first call."""
        self._entered_count += 1
        if self._session is None:
            super().__enter__()
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Only close when the outermost context exits."""
        self._entered_count -= 1
        if self._entered_count <= 0:
            super().__exit__(exc_type, exc_val, exc_tb)
            self._entered_count = 0


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def e2e_settings() -> Settings:
    """Default E2E test settings using SQLite in-memory."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=False,
        HOST="127.0.0.1",
        PORT=8000,
        DATABASE_URL="sqlite:///:memory:",
        CORS_ORIGINS=[],
        LOG_LEVEL="WARNING",
        LOG_FORMAT="text",
        SECRET_KEY="e2e-test-secret-key",
        ALLOWED_HOSTS=["*"],
        SECURITY_HEADERS_ENABLED=False,
    )


@pytest.fixture
def e2e_engine(e2e_settings):
    """Create a real SQLAlchemy engine with tables created.

    Uses check_same_thread=False for SQLite in-memory with async.
    StaticPool ensures all sessions share the same connection.
    """
    engine = sa_create_engine(
        e2e_settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def e2e_session_factory(e2e_engine) -> sessionmaker:
    """Create a real sessionmaker bound to the E2E engine."""
    return sessionmaker(bind=e2e_engine, expire_on_commit=False)


@pytest.fixture
def e2e_uow(e2e_session_factory):
    """Create a PerfUnitOfWork for use in DI override.

    Returns a callable that creates fresh PerfUnitOfWork instances
    per request and manages the lifecycle (enter → yield → exit).
    """
    from ingestion.presentation.dependencies import get_event_publisher

    def _make_uow(
        session_factory: sessionmaker = Depends(
            lambda: e2e_session_factory
        ),
        event_publisher=None,
    ):
        ep = get_event_publisher()
        uow = PerfUnitOfWork(
            session_factory=session_factory,
            event_publisher=ep,
        )
        with uow:
            yield uow

    return _make_uow


@pytest.fixture
def e2e_app(e2e_settings, e2e_engine, e2e_session_factory, e2e_uow):
    """Build FastAPI app with real infrastructure for E2E tests.

    Uses create_app() to get full middleware stack, routers, exception
    handlers. Overrides get_uow DI to use PerfUnitOfWork (idempotent
    enter for SQLite StaticPool safety).
    """
    from ingestion.presentation.app import create_app
    from ingestion.presentation.dependencies import get_uow

    app = create_app(settings=e2e_settings)

    # Override engine/session_factory on app.state to use our E2E fixtures
    app.state.engine = e2e_engine
    app.state.session_factory = e2e_session_factory

    # Override get_uow to use PerfUnitOfWork (handles SQLite double-enter)
    app.dependency_overrides[get_uow] = e2e_uow

    return app


@pytest.fixture
async def e2e_client(e2e_app) -> AsyncClient:
    """Async httpx client wired to the E2E app."""
    transport = ASGITransport(app=e2e_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
