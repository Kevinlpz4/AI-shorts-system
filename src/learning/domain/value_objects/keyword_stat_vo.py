"""
KeywordStat Value Object — Immutable statistics for a single keyword.

Tracks how often a keyword appears in content and how often it was approved.
Used inside SourceQualityProfile to build per-keyword quality profiles.
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class KeywordStat(ValueObject):
    """Immutable keyword statistics.

    Attributes:
        keyword: The keyword being tracked.
        count: Total number of times this keyword appeared in content.
        approved_count: Number of times content with this keyword was approved.

    Invariants:
        - keyword MUST NOT be empty.
        - count MUST be >= 0.
        - approved_count MUST be >= 0.
        - approved_count MUST be <= count.
    """

    keyword: str
    count: int
    approved_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.keyword, str) or not self.keyword.strip():
            raise ValueError("KeywordStat.keyword must not be empty")
        if not isinstance(self.count, int) or self.count < 0:
            raise ValueError(
                f"KeywordStat.count must be >= 0, got {self.count}"
            )
        if not isinstance(self.approved_count, int) or self.approved_count < 0:
            raise ValueError(
                f"KeywordStat.approved_count must be >= 0, got {self.approved_count}"
            )
        if self.approved_count > self.count:
            raise ValueError(
                f"KeywordStat.approved_count ({self.approved_count}) "
                f"must be <= count ({self.count})"
            )

    @property
    def approval_rate(self) -> float:
        """Approval rate for this keyword (0.0 if no occurrences)."""
        if self.count == 0:
            return 0.0
        return self.approved_count / self.count

    @property
    def is_effective(self) -> bool:
        """True if keyword has sufficient data and high approval rate (>= 0.7)."""
        return self.count >= 5 and self.approval_rate >= 0.7
