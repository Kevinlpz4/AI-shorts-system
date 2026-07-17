"""
ScoreWeights Value Object — Adaptive scoring weight configuration.

Encapsulates the four scoring dimensions used to compute final article scores.
All weights MUST sum to 1.0 (±0.01 tolerance) and each MUST be in [0.0, 1.0].
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject

SUM_TOLERANCE = 0.01


@dataclass(frozen=True)
class ScoreWeights(ValueObject):
    """Immutable scoring weight configuration.

    Attributes:
        relevance: Weight for content relevance to topic (0.0-1.0).
        popularity: Weight for content popularity signals (0.0-1.0).
        recency: Weight for content freshness/recency (0.0-1.0).
        source_reliability: Weight for source reliability (0.0-1.0).

    Invariants:
        - All weights MUST be in [0.0, 1.0].
        - Sum of all weights MUST be 1.0 (±0.01 tolerance).
    """

    relevance: float
    popularity: float
    recency: float
    source_reliability: float

    def __post_init__(self) -> None:
        for name in ("relevance", "popularity", "recency", "source_reliability"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"ScoreWeights.{name} must be a number, got {type(value).__name__}"
                )
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"ScoreWeights.{name} must be in [0.0, 1.0], got {value}"
                )

        total = self.relevance + self.popularity + self.recency + self.source_reliability
        if abs(total - 1.0) > SUM_TOLERANCE:
            raise ValueError(
                f"ScoreWeights must sum to 1.0 (±{SUM_TOLERANCE}), got {total:.4f}"
            )

    @property
    def total(self) -> float:
        """Sum of all weights."""
        return self.relevance + self.popularity + self.recency + self.source_reliability

    def as_dict(self) -> dict[str, float]:
        """Serialize weights to a dictionary."""
        return {
            "relevance": self.relevance,
            "popularity": self.popularity,
            "recency": self.recency,
            "source_reliability": self.source_reliability,
        }
