"""
Entity — Base class for Domain Entities.

Entity provides identity-based equality following DDD principles:
    - Every Entity has an explicit ``id`` of type ``EntityId``
    - Two Entities are equal IFF they have the same type AND the same id
    - ``__hash__`` depends exclusively on ``EntityId``
    - Entities are mutable (they have a lifecycle)

Equality rules:
    - ``type(self) is type(other)`` — strict type check (no isinstance)
    - ``self.id == other.id`` — same identity value
    - Returns ``NotImplemented`` for different types (allows Python's
      reflected operation protocol)

Design decision (see Sprint 2.2 Spec §7.1):
    Uses ``type(self) is type(other)`` instead of ``isinstance`` for:
    1. Consistency with EntityId (Sprint 2.1)
    2. Symmetry: Entity != AggregateRoot with same id
    3. Semantic precision: different entity types are NEVER equal

NOTE: The ``id`` field has NO default value. Every Entity MUST receive
an explicit ``EntityId`` at construction time. This is deliberate — in DDD,
identity is assigned at creation time and should not be auto-generated.
"""

from dataclasses import dataclass

from foundation.entity_id import EntityId


@dataclass
class Entity:
    """
    Base class for all Domain Entities in the system.

    Attributes:
        id: The Entity's unique identifier. Must be provided at construction.

    Responsibilities:
        - Identity-based equality (type-strict + same id)
        - Hash based exclusively on EntityId
        - Mutable — subclasses can add attributes with lifecycle

    Does NOT do:
        - Does NOT have domain events (use AggregateRoot for that)
        - Does NOT have persistence logic
        - Does NOT have automatic validation
    """
    id: EntityId  # no default — identity MUST be explicit

    def __eq__(self, other: object) -> bool:
        """Two entities are equal IFF same type AND same id."""
        if type(self) is not type(other):
            return NotImplemented
        return self.id == other.id  # type: ignore[union-attr]

    def __hash__(self) -> int:
        """Hash depends EXCLUSIVELY on EntityId."""
        return hash(self.id)
