"""SQLAlchemy TypeDecorators for Domain Types.

This module is DESIGNED TO BE REUSABLE. It imports nothing from Ingestion
or any Bounded Context (except ``EntityId`` from Foundation, which is a
cross-cutting concern). It can be extracted verbatim when needed.

Current TypeDecorators
----------------------
* ``EntityIdType[T]`` — Generic decorator for ANY ``EntityId`` subclass.
  Add more decorators here (ValueObjectType, EnumType, etc.) as sprints
  progress.

Usage::

    from ingestion.infrastructure.persistence import EntityIdType


    class MyModel(PersistenceBase):
        __tablename__ = "my_table"

        id: Mapped[SourceId] = mapped_column(
            EntityIdType(SourceId), primary_key=True
        )

The ORM column receives and returns ``SourceId`` objects transparently.
The database stores ``UUID`` values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from sqlalchemy.types import TypeDecorator, Uuid

from foundation.entity_id import EntityId

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect

T = TypeVar("T", bound=EntityId)


class EntityIdType(TypeDecorator[T], Generic[T]):
    """Generic SQLAlchemy TypeDecorator for any ``EntityId`` subclass.

    This is a **single, reusable** decorator that works with ALL ``EntityId``
    subtypes (SourceId, FeedId, RawArticleId, CategoryId, TopicId, etc.)

    It does NOT know about any specific ID class. Instead, it receives the
    concrete ``EntityId`` subclass at construction time::

        # In an ORM model:
        id: Mapped[SourceId] = mapped_column(
            EntityIdType(SourceId), primary_key=True
        )

        source_id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId))

    How it works::

        Python (EntityId)  ──bind──▶  Database (UUID)
        Python (EntityId)  ◀─result──  Database (UUID)

    The domain layer never sees ``UUID`` values. Every read returns the
    correct ``EntityId`` subclass. Every write receives the subclass and
    converts to ``UUID`` for the database.

    Args:
        id_type: The concrete ``EntityId`` class (e.g., ``SourceId``,
            ``FeedId``). Used to reconstruct the correct type on reads.
    """

    impl = Uuid
    """Underlying SQLAlchemy type. ``Uuid`` is portable across all
    supported databases (SQLite, PostgreSQL)."""

    cache_ok = True
    """Allow SQLAlchemy to cache this type. Safe because the conversion
    logic is deterministic and side-effect-free."""

    def __init__(self, id_type: type[T]) -> None:
        """Initialize the decorator with the concrete EntityId class.

        Args:
            id_type: The EntityId subclass to construct on read.
                     Pass the class, not an instance.

        Raises:
            TypeError: If ``id_type`` is not a subclass of ``EntityId``.
        """
        if not (isinstance(id_type, type) and issubclass(id_type, EntityId)):
            raise TypeError(
                f"id_type must be a subclass of EntityId, got {id_type!r}"
            )
        self._id_type: type[T] = id_type
        super().__init__()

    def process_bind_param(  # type: ignore[override]
        self,
        value: T | None,
        dialect: Dialect,
    ) -> UUID | None:
        """Convert ``EntityId → UUID`` before writing to the database.

        Args:
            value: The ``EntityId`` instance (or ``None``).
            dialect: The current SQL dialect (unused).

        Returns:
            The inner ``UUID`` value, or ``None``.
        """
        if value is None:
            return None
        return value.value

    def process_result_value(  # type: ignore[override]
        self,
        value: UUID | None,
        dialect: Dialect,
    ) -> T | None:
        """Reconstruct ``EntityId`` from ``UUID`` when reading from DB.

        Args:
            value: The ``UUID`` from the database (or ``None``).
            dialect: The current SQL dialect (unused).

        Returns:
            An instance of ``self._id_type`` wrapping the UUID, or ``None``.
        """
        if value is None:
            return None
        return self._id_type(value=value)
