"""
Confidence Value Object — Encapsulates confidence level with sample size.

Confidence represents how certain the system is about a prediction or signal.
Higher sample sizes increase confidence, but confidence itself is bounded [0.0, 1.0].
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class Confidence(ValueObject):
    """Immutable confidence level with associated sample size.

    Attributes:
        value: Confidence level between 0.0 (no confidence) and 1.0 (absolute).
        sample_size: Number of data points used to compute confidence.

    Invariants:
        - value MUST be in [0.0, 1.0]
        - sample_size MUST be >= 0
    """

    value: float
    sample_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError(
                f"Confidence.value must be a number, got {type(self.value).__name__}"
            )
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"Confidence.value must be in [0.0, 1.0], got {self.value}"
            )
        if not isinstance(self.sample_size, int):
            raise TypeError(
                f"Confidence.sample_size must be an int, got {type(self.sample_size).__name__}"
            )
        if self.sample_size < 0:
            raise ValueError(
                f"Confidence.sample_size must be >= 0, got {self.sample_size}"
            )

    @property
    def is_high(self) -> bool:
        """True if confidence is >= 0.8."""
        return self.value >= 0.8

    @property
    def is_reliable(self) -> bool:
        """True if confidence is high AND sample size is sufficient (>= 30)."""
        return self.is_high and self.sample_size >= 30
