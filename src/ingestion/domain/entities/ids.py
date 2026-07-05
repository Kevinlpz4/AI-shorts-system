"""
Entity IDs for the Ingestion Bounded Context.

Every ID inherits from ``EntityId`` (Foundation) and provides:
  - ``from_string(value: str) -> Self`` — construct from string
  - ``generate() -> Self`` — create with new random UUID
  - ``__str__() -> str`` — string representation
  - Type-safety: ``SourceId(x) != FeedId(x)`` even with same UUID

Following ADR-021, these IDs live in Ingestion BC (not Foundation) because
they are only used by this BC.
"""

from __future__ import annotations

from typing import Self

from foundation.entity_id import EntityId


class SourceId(EntityId):
    """Identity for a NewsSource aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new SourceId with a random UUID."""
        return cls()


class FeedId(EntityId):
    """Identity for a Feed aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new FeedId with a random UUID."""
        return cls()


class RawArticleId(EntityId):
    """Identity for a RawArticle aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new RawArticleId with a random UUID."""
        return cls()


class CategoryId(EntityId):
    """Identity for a Category entity."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new CategoryId with a random UUID."""
        return cls()


class TopicId(EntityId):
    """Identity for a Topic entity."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new TopicId with a random UUID."""
        return cls()
