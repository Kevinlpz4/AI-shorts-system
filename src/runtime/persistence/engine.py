"""
RuntimeEngine — SQLAlchemy engine factory for Runtime persistence.

Usage::

    from runtime.persistence.engine import RuntimeEngine

    engine = RuntimeEngine("postgresql+psycopg2://localhost:5432/ai_shorts")
    engine.create_tables()
    session = engine.get_session()
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from runtime.persistence.models import _RuntimeBase


class RuntimeEngine:
    """Factory for creating SQLAlchemy engines and sessions.

    Wraps engine creation with ``pool_pre_ping=True`` for connection
    health checks. Provides table creation and session factory.

    Args:
        database_url: SQLAlchemy database connection URL.
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self._engine)

    def create_tables(self) -> None:
        """Create all tables defined in Runtime ORM models."""
        _RuntimeBase.metadata.create_all(self._engine)

    def get_session(self) -> Session:
        """Create and return a new SQLAlchemy session.

        The caller is responsible for closing the session.
        """
        return self._session_factory()
