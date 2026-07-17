"""
Entity IDs for the Learning Bounded Context.

Every ID inherits from ``EntityId`` (Foundation) and provides:
  - ``from_string(value: str) -> Self`` — construct from string
  - ``generate() -> Self`` — create with new random UUID
  - ``__str__() -> str`` — string representation
  - Type-safety: ``FeedbackId(x) != LearningSignalId(x)`` even with same UUID

Following ADR-021, these IDs live in Learning BC (not Foundation) because
they are only used by this BC.
"""
from __future__ import annotations

from typing import Self

from foundation.entity_id import EntityId


class FeedbackId(EntityId):
    """Identity for a FeedbackRecord aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new FeedbackId with a random UUID."""
        return cls()


class LearningSignalId(EntityId):
    """Identity for a LearningSignal aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new LearningSignalId with a random UUID."""
        return cls()


class SourceQualityId(EntityId):
    """Identity for a SourceQualityProfile aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new SourceQualityId with a random UUID."""
        return cls()


class LearningModelId(EntityId):
    """Identity for a LearningModel aggregate root."""

    @classmethod
    def generate(cls) -> Self:
        """Create a new LearningModelId with a random UUID."""
        return cls()
