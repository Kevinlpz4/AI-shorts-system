"""Engine and session factory for SQLAlchemy.

This module is DESIGNED TO BE REUSABLE. It imports nothing from Ingestion
or any Bounded Context. It can be extracted verbatim to a shared package.

Naming follows ``create_engine()`` (not ``create_sync_engine()``) to keep
the API short today and leave room for an async variant later::

    # Sync (today):
    engine = create_engine("sqlite:///data.db")
    session_factory = create_session_factory(engine)

    # Async (future):
    engine = create_async_engine("postgresql+asyncpg://...")
    async_session_factory = create_async_session_factory(engine)
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine as _sa_create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine(url: str, **kwargs: Any) -> Engine:
    """Create a SQLAlchemy Engine from a database URL.

    Accepts ANY valid SQLAlchemy database URL:
        * ``sqlite:///:memory:`` — in-memory SQLite (testing)
        * ``sqlite+pysqlite:///data.db`` — file-based SQLite
        * ``postgresql+psycopg://user:pass@host/db`` — PostgreSQL
        * ``postgresql:///...`` — any other dialect

    There is NO dialect-specific logic here. The engine is configured
    purely through the URL and ``**kwargs``, keeping this function
    completely generic and reusable.

    Common keyword arguments::

        echo=True              — log all SQL (development)
        pool_size=5            — connection pool size
        max_overflow=10        — overflow connections
        pool_pre_ping=True     — verify connections before use
        pool_recycle=3600      — recycle connections after N seconds

    Note:
        This function returns a **sync** engine. For async support,
        use :func:`create_async_engine` (available in a future sprint).

    Example::

        # In-memory SQLite (testing):
        engine = create_engine("sqlite:///:memory:")

        # PostgreSQL (production):
        engine = create_engine(
            "postgresql+psycopg://user:pass@localhost:5432/mydb",
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    """
    return _sa_create_engine(url, **kwargs)


def create_session_factory(
    engine: Engine,
    *,
    expire_on_commit: bool = False,
    **kwargs: Any,
) -> sessionmaker[Session]:
    """Create a sessionmaker bound to the given engine.

    Args:
        engine: The SQLAlchemy Engine to bind.
        expire_on_commit: ``False`` by default — prevents automatic
            expiration of loaded objects after commit. Set to ``True`` if
            you need the ORM to refresh objects on next access.
        **kwargs: Additional arguments forwarded to ``sessionmaker``.

    Returns:
        A ``sessionmaker[Session]`` factory. Call it to get a new ``Session``::

            Session = create_session_factory(engine)
            with Session() as session:
                session.add(my_model)
                session.commit()

    Note:
        ``expire_on_commit=False`` is the recommended default for
        application code. Avoid the "expire on commit then lazy-load"
        anti-pattern by keeping objects usable after commit.
    """
    return sessionmaker(
        bind=engine,
        expire_on_commit=expire_on_commit,
        **kwargs,
    )
