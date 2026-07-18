"""
DeclarativeBase for Learning BC SQLAlchemy models.

All learning tables live in the ``learning`` schema.
Uses SQLAlchemy 2.0 style with ``DeclarativeBase``.
"""
from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for constraints — ensures Alembic generates
# deterministic constraint names for indexes, unique constraints, etc.
NAMING_CONVENTION = {
    "ix": "idx_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """DeclarativeBase for all Learning BC models."""

    metadata = MetaData(
        naming_convention=NAMING_CONVENTION,
    )
