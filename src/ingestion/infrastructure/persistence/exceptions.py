"""Persistence exception hierarchy.

This module is DESIGNED TO BE REUSABLE. It imports nothing from Ingestion
or any Bounded Context (except ``DomainError`` from Foundation, which is a
cross-cutting concern for structured error handling).

Base ``PersistenceError`` inherits from ``RuntimeError`` (not ``Exception``)
to make it distinct from domain and application errors in ``except`` clauses.
"""

from __future__ import annotations


class PersistenceError(RuntimeError):
    """Base exception for all persistence-layer errors.

    Use this as a catch-all for infrastructure issues::

        try:
            session.commit()
        except PersistenceError:
            handle_infrastructure_error()

    Subclass for more specific failures.
    """


class EntityNotFoundError(PersistenceError):
    """Raised when a database query returns no matching row.

    This is the persistence equivalent of a 404 — the requested entity
    does not exist in the database. It is intentionally distinct from
    domain-level "not found" errors so that infrastructure can be
    replaced without changing error handling in higher layers.

    Example::

        raise EntityNotFoundError("Source", str(source_id))
    """

    def __init__(self, entity_name: str, entity_id: str) -> None:
        """Initialize with entity metadata.

        Args:
            entity_name: Human-readable entity type name (e.g., "Source").
            entity_id: The identifier that was not found (string form).
        """
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} not found: {entity_id}")


class DuplicateEntityError(PersistenceError):
    """Raised when a unique constraint is violated.

    Typically wraps SQLAlchemy's ``IntegrityError`` for cases where the
    error originates from a ``UNIQUE`` or ``PRIMARY KEY`` constraint::

        raise DuplicateEntityError("Source", "name", "my-source")
    """

    def __init__(
        self,
        entity_name: str,
        field: str,
        value: str,
    ) -> None:
        """Initialize with conflict metadata.

        Args:
            entity_name: Human-readable entity type name.
            field: The field that caused the conflict (e.g., "name", "slug").
            value: The conflicting value.
        """
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(f"Duplicate {entity_name}.{field}: {value}")


class ConcurrentModificationError(PersistenceError):
    """Raised when an optimistic locking conflict is detected.

    Wraps SQLAlchemy's ``StaleDataError`` when a ``version_id_col``
    check fails during flush/commit. Indicates that another transaction
    modified the same entity concurrently.

    Example::

        raise ConcurrentModificationError("Source", str(source_id))
    """

    def __init__(self, entity_name: str, entity_id: str) -> None:
        """Initialize with entity metadata.

        Args:
            entity_name: Human-readable entity type name (e.g., "Source").
            entity_id: The identifier of the entity with the conflict.
        """
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(
            f"Concurrent modification on {entity_name} '{entity_id}'",
        )
