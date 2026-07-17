"""
KeywordStat Entity — Lightweight entity for keyword statistics persistence.

Wraps the KeywordStat value object with an entity ID for standalone
persistence in the database. This enables tracking keyword statistics
across the entire system, not just within a SourceQualityProfile.

NOTE: For inline usage within SourceQualityProfile, use the
KeywordStat value object directly (value_objects/keyword_stat_vo.py).
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.entity import Entity

from learning.domain.entities.ids import LearningSignalId
from learning.domain.value_objects.keyword_stat_vo import KeywordStat


@dataclass(eq=False)
class KeywordStatEntity(Entity):
    """Entity wrapper for KeywordStat with its own identity.

    This allows keyword statistics to be persisted independently
    and queried across source quality profiles.

    Attributes:
        id: Entity identity (LearningSignalId for persistence).
        keyword_stat: The underlying keyword statistics value object.
    """

    id: LearningSignalId
    keyword_stat: KeywordStat

    @classmethod
    def create(cls, keyword: str, count: int, approved_count: int) -> KeywordStatEntity:
        """Factory method to create a KeywordStatEntity from raw values.

        Args:
            keyword: The keyword being tracked.
            count: Total occurrences.
            approved_count: Approved occurrences.

        Returns:
            New KeywordStatEntity with generated ID.
        """
        return cls(
            id=LearningSignalId.generate(),
            keyword_stat=KeywordStat(
                keyword=keyword,
                count=count,
                approved_count=approved_count,
            ),
        )

    @property
    def keyword(self) -> str:
        """Delegate to keyword_stat."""
        return self.keyword_stat.keyword

    @property
    def count(self) -> int:
        """Delegate to keyword_stat."""
        return self.keyword_stat.count

    @property
    def approved_count(self) -> int:
        """Delegate to keyword_stat."""
        return self.keyword_stat.approved_count

    @property
    def approval_rate(self) -> float:
        """Delegate to keyword_stat."""
        return self.keyword_stat.approval_rate
