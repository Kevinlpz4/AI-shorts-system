"""
FeatureSnapshot Value Object — Immutable snapshot of all scoring features at a point in time.

Captures enough data for historical reproducibility of a scoring decision.
All float fields except timestamp (datetime).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class FeatureSnapshot(ValueObject):
    """Immutable snapshot of scoring features at decision time.

    Provides historical reproducibility — given the same snapshot,
    the same decision should be reproducible.

    Attributes:
        base_score: Base content quality score (0.0-1.0).
        freshness_score: Time-based freshness score (0.0-1.0).
        keyword_bonus: Bonus from keyword matching (0.0-1.0).
        source_bonus: Bonus from source reliability (0.0-1.0).
        topic_penalty: Penalty from topic mismatch (0.0-1.0).
        confidence: Confidence in the scoring (0.0-1.0).
        final_score: Computed final score (0.0-1.0).
        timestamp: When this snapshot was captured.

    Invariants:
        - All float fields MUST be in [0.0, 1.0].
        - timestamp MUST be a datetime.
    """

    base_score: float
    freshness_score: float
    keyword_bonus: float
    source_bonus: float
    topic_penalty: float
    confidence: float
    final_score: float
    timestamp: datetime

    def __post_init__(self) -> None:
        float_fields = (
            "base_score",
            "freshness_score",
            "keyword_bonus",
            "source_bonus",
            "topic_penalty",
            "confidence",
            "final_score",
        )
        for name in float_fields:
            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"FeatureSnapshot.{name} must be a number, got {type(value).__name__}"
                )
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"FeatureSnapshot.{name} must be in [0.0, 1.0], got {value}"
                )

        if not isinstance(self.timestamp, datetime):
            raise TypeError(
                f"FeatureSnapshot.timestamp must be a datetime, got {type(self.timestamp).__name__}"
            )

    def as_dict(self) -> dict[str, float | datetime]:
        """Serialize snapshot to a dictionary."""
        return {
            "base_score": self.base_score,
            "freshness_score": self.freshness_score,
            "keyword_bonus": self.keyword_bonus,
            "source_bonus": self.source_bonus,
            "topic_penalty": self.topic_penalty,
            "confidence": self.confidence,
            "final_score": self.final_score,
            "timestamp": self.timestamp,
        }
