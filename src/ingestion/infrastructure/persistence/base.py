"""SQLAlchemy DeclarativeBase with strict naming conventions.

This module is DESIGNED TO BE REUSABLE. It imports nothing from Ingestion,
``foundation``, or any Bounded Context. It can be extracted verbatim to a
shared infrastructure package when a second BC needs persistence.

Usage::

    from ingestion.infrastructure.persistence import PersistenceBase


    class MyModel(PersistenceBase):
        __tablename__ = "my_table"
        ...
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# ── Naming Convention ──────────────────────────────────────────────────────

naming_convention: dict[str, str] = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}
"""Strict, predictable naming convention for all database constraints.

This convention is compatible with Alembic's ``--autogenerate`` and ensures
that all constraint names are deterministic across environments:

    ==================  ============================================
    Prefix              Pattern
    ==================  ============================================
    ``pk_``             ``pk_<table>``
    ``fk_``             ``fk_<table>_<referenced>``
    ``uq_``             ``uq_<table>_<column>``
    ``ix_``             ``ix_<table>_<column>``
    ``ck_``             ``ck_<table>_<rule>``
    ==================  ============================================

Usage with Alembic::

    # alembic/env.py
    from ingestion.infrastructure.persistence import naming_convention

    target_metadata = PersistenceBase.metadata

    # Alembic will read naming_convention from metadata automatically.
"""


# ── Declarative Base ───────────────────────────────────────────────────────

class PersistenceBase(DeclarativeBase):
    """Abstract base for all ORM models.

    All model classes MUST inherit from this base. It provides:

    * A shared ``MetaData`` instance with the project-wide naming convention.
    * Compatibility with Alembic ``--autogenerate``.
    * A single registry for all mapped classes.

    Note:
        This class is abstract. It should never be instantiated directly.
        Use it as the base class for concrete ORM models::

            class NewsSourceModel(PersistenceBase):
                __tablename__ = "ingestion_news_sources"
                ...
    """

    metadata = MetaData(naming_convention=naming_convention)
