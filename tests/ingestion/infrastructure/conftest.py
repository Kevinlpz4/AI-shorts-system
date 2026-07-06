"""
Test fixtures for Ingestion Infrastructure Layer tests.

Includes shared persistence fixtures that support parametrized engine
factories (SQLite today, PostgreSQL in the future).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import Engine, event, text
from sqlalchemy.orm import Session, sessionmaker

# Ensure src/ is on sys.path for ingestion imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


# ══════════════════════════════════════════════════════════════════════════════
# Persistence Fixtures (Sprint 5.1)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sqlite_engine():
    """Create a SQLite in-memory engine for testing.

    The engine is disposed of after each test to ensure isolation.
    """
    from ingestion.infrastructure.persistence import create_engine

    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def sqlite_session_factory(sqlite_engine):
    """Create a sessionmaker bound to the SQLite engine."""
    from ingestion.infrastructure.persistence import create_session_factory

    return create_session_factory(sqlite_engine)


@pytest.fixture
def sqlite_session(sqlite_session_factory):
    """Provide a clean session for each test.

    Rolls back after each test to prevent cross-test pollution.
    """
    session: Session = sqlite_session_factory()
    yield session
    session.rollback()
    session.close()


# ── Parametrized Engine Factory ──────────────────────────────────────────

ENGINE_FACTORIES = [
    pytest.param(
        lambda: _create_sqlite_engine_with_fk(),
        id="sqlite",
        marks=[pytest.mark.unit],
    ),
    # ── PostgreSQL will be added here when available ───────────────────────
    # pytest.param(
    #     lambda: create_engine("postgresql+psycopg://user:pass@localhost:5432/test"),
    #     id="postgres",
    #     marks=[pytest.mark.postgres, pytest.mark.integration],
    # ),
]


def _create_sqlite_engine_with_fk():
    """Create a SQLite engine with foreign key enforcement enabled.

    SQLite requires ``PRAGMA foreign_keys = ON`` per-connection.
    This listener ensures FK constraints are enforced in tests.
    """
    from ingestion.infrastructure.persistence import create_engine

    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


@pytest.fixture(params=ENGINE_FACTORIES)
def engine_factory(request):
    """Parametrized engine factory for cross-dialect testing.

    Usage::

        def test_thing(engine_factory):
            engine = engine_factory()
            # ... test with engine

    When PostgreSQL is added, tests using this fixture will automatically
    run against both dialects with zero code changes.
    """
    return request.param


@pytest.fixture
def engine(engine_factory):
    """Convenience fixture: a fresh engine from the parametrized factory.

    Tests that need just an engine (not the factory) can use this directly.
    """
    eng: Engine = engine_factory()
    yield eng
    eng.dispose()


@pytest.fixture
def engine_session(engine):
    """Convenience fixture: a session bound to the parametrized engine.

    Rolls back after each test.
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── Table Creation Helper ────────────────────────────────────────────────

@pytest.fixture
def tables(engine):
    """Create all tables from PersistenceBase metadata on the engine.

    Usage::

        def test_with_tables(engine, tables, engine_session):
            # engine_session has all tables created
            ...

    The fixture is scoped per-test so tests can mutate tables independently
    without interference.
    """
    from ingestion.infrastructure.persistence import PersistenceBase

    PersistenceBase.metadata.create_all(engine)
    yield
    PersistenceBase.metadata.drop_all(engine)


# ── Unit of Work Fixture ────────────────────────────────────────────────


@pytest.fixture
def uow(sqlite_session_factory, tables):
    """Fresh SQLAlchemyUnitOfWork with SQLite in-memory + schema.

    Usage::

        def test_something(uow):
            with uow:
                uow.news_sources.save(...)
                uow.commit()
    """
    from ingestion.infrastructure.persistence import SQLAlchemyUnitOfWork

    return SQLAlchemyUnitOfWork(sqlite_session_factory)
