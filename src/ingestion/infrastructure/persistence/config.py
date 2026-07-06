"""Persistence configuration via Pydantic Settings.

This module IS Ingestion-specific (it lives in the Ingestion BC), but its
pattern — a ``BaseSettings`` subclass with typed fields — can be replicated
in any BC that needs persistence.

The settings are read from environment variables or ``.env`` files using
Pydantic's standard resolution order:

    1. Environment variable (highest priority)
    2. ``.env`` file in the project root
    3. Default value (lowest priority)

Example ``.env`` file::

    INGESTION_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/ingestion
    INGESTION_DATABASE_ECHO=true
    INGESTION_DATABASE_POOL_SIZE=10
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    """Configuration for the Ingestion BC persistence layer.

    All fields have sensible defaults for local development (SQLite).
    Override via environment variables with the ``INGESTION_`` prefix
    or a ``.env`` file.

    Example::

        settings = IngestionSettings()
        engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
        )
    """

    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────

    database_url: str = "sqlite:///:memory:"
    """Database connection URL.

    Supports any SQLAlchemy-compatible URL:

    * ``sqlite:///:memory:`` — in-memory SQLite (default, for testing)
    * ``sqlite+pysqlite:///data.db`` — file-based SQLite
    * ``postgresql+psycopg://user:pass@host:5432/db`` — PostgreSQL
    """

    database_echo: bool = False
    """Log all SQL statements to stderr. Useful for debugging during
    development. Always ``False`` in production."""

    # ── Connection Pool ───────────────────────────────────────────────────

    database_pool_size: int = 5
    """Number of connections to maintain in the pool.

    SQLAlchemy default is 5. For production PostgreSQL, adjust based on
    the number of application workers::

        pool_size = max(5, 100 // num_workers)
    """

    database_max_overflow: int = 10
    """Maximum number of overflow connections beyond ``pool_size``.

    Overflow connections are created temporarily when the pool is
    exhausted. They are closed and discarded after use.
    """

    database_pool_pre_ping: bool = True
    """Verify a connection is alive before using it from the pool.

    This prevents serving stale connections to the application. The
    overhead is one round-trip per connection acquisition (a ``SELECT 1``).
    Recommended for all production databases.
    """

    database_pool_recycle: int = 3600
    """Recycle connections after this many seconds (default: 1 hour).

    Prevents connection drops from firewalls, load balancers, or
    database-side timeouts. Set to 300 (5 minutes) if behind PgBouncer.
    """
