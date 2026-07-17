"""
SourceQualityProfile — Aggregate Root tracking cumulative quality per source.

Maintains running statistics about how content from each source is received
by human reviewers, enabling source-reliability signals.

Invariants:
  - I-01: All counts MUST be non-negative
  - I-02: approval_rate MUST be in [0.0, 1.0] (computed: approved / total)
  - I-03: total_decisions MUST equal sum of all decision counts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from foundation.base.aggregate_root import AggregateRoot

from learning.domain.entities.ids import SourceQualityId
from learning.domain.exceptions import LearningDomainError
from learning.domain.value_objects.keyword_stat_vo import KeywordStat


@dataclass(eq=False, init=False)
class SourceQualityProfile(AggregateRoot):
    """Cumulative quality profile for a single content source.

    Tracks how often content from a given source is approved, rejected,
    auto-approved, auto-rejected, or overridden. Also maintains per-keyword
    effectiveness statistics.

    Attributes:
        id: Unique identity.
        source_name: Name of the source (unique).
        total_decisions: Total number of decisions for this source.
        approved_count: Number of human approvals.
        rejected_count: Number of human rejections.
        auto_approved_count: Number of auto-approvals.
        auto_rejected_count: Number of auto-rejections.
        overridden_count: Number of overridden decisions.
        approval_rate: Computed rate of approvals (approved / total).
        keywords: Per-keyword statistics (keyword text → KeywordStat).
        last_updated: When this profile was last updated.
    """

    id: SourceQualityId
    source_name: str
    total_decisions: int
    approved_count: int
    rejected_count: int
    auto_approved_count: int
    auto_rejected_count: int
    overridden_count: int
    approval_rate: float
    keywords: dict[str, KeywordStat]
    last_updated: datetime

    def __init__(
        self,
        id: SourceQualityId,
        source_name: str,
        total_decisions: int = 0,
        approved_count: int = 0,
        rejected_count: int = 0,
        auto_approved_count: int = 0,
        auto_rejected_count: int = 0,
        overridden_count: int = 0,
        keywords: dict[str, KeywordStat] | None = None,
        last_updated: datetime | None = None,
    ) -> None:
        """Initialize a SourceQualityProfile.

        Args:
            id: Unique identity.
            source_name: Name of the source.
            total_decisions: Total decisions (default: 0).
            approved_count: Human approvals (default: 0).
            rejected_count: Human rejections (default: 0).
            auto_approved_count: Auto-approvals (default: 0).
            auto_rejected_count: Auto-rejections (default: 0).
            overridden_count: Overridden decisions (default: 0).
            keywords: Per-keyword stats (default: empty dict).
            last_updated: Last update timestamp (default: now UTC).

        Raises:
            LearningDomainError: If invariants are violated.
        """
        from datetime import datetime, timezone

        # I-01: All counts non-negative
        counts = {
            "total_decisions": total_decisions,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "auto_approved_count": auto_approved_count,
            "auto_rejected_count": auto_rejected_count,
            "overridden_count": overridden_count,
        }
        for name, value in counts.items():
            if value < 0:
                raise LearningDomainError(
                    f"SourceQualityProfile.{name} must be >= 0, got {value} (I-01)"
                )

        # I-03: total_decisions must equal sum of decision counts
        sum_counts = (
            approved_count
            + rejected_count
            + auto_approved_count
            + auto_rejected_count
            + overridden_count
        )
        if total_decisions != sum_counts:
            raise LearningDomainError(
                f"SourceQualityProfile.total_decisions ({total_decisions}) must equal "
                f"sum of counts ({sum_counts}) (I-03)"
            )

        # Validate source_name not empty
        if not source_name or not source_name.strip():
            raise LearningDomainError(
                "SourceQualityProfile.source_name must not be empty"
            )

        # I-02: Compute approval_rate
        if total_decisions > 0:
            approval_rate = approved_count / total_decisions
        else:
            approval_rate = 0.0

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source_name", source_name.strip())
        object.__setattr__(self, "total_decisions", total_decisions)
        object.__setattr__(self, "approved_count", approved_count)
        object.__setattr__(self, "rejected_count", rejected_count)
        object.__setattr__(self, "auto_approved_count", auto_approved_count)
        object.__setattr__(self, "auto_rejected_count", auto_rejected_count)
        object.__setattr__(self, "overridden_count", overridden_count)
        object.__setattr__(self, "approval_rate", approval_rate)
        object.__setattr__(self, "keywords", keywords or {})
        object.__setattr__(
            self,
            "last_updated",
            last_updated or datetime.now(timezone.utc),
        )
        # Initialize AggregateRoot._events
        object.__setattr__(self, "_events", [])

    def record_decision(
        self,
        decision_type: str,
        keywords: list[str] | None = None,
    ) -> None:
        """Record a new decision and update counts.

        Args:
            decision_type: One of 'approved', 'rejected', 'auto_approved',
                'auto_rejected', 'overridden'.
            keywords: List of keywords to update stats for.

        Raises:
            LearningDomainError: If decision_type is invalid.
        """
        from datetime import datetime, timezone

        count_map = {
            "approved": "approved_count",
            "rejected": "rejected_count",
            "auto_approved": "auto_approved_count",
            "auto_rejected": "auto_rejected_count",
            "overridden": "overridden_count",
        }

        if decision_type not in count_map:
            raise LearningDomainError(
                f"Invalid decision_type: '{decision_type}'. "
                f"Expected one of: {list(count_map.keys())}"
            )

        # Increment the specific count
        attr_name = count_map[decision_type]
        new_value = getattr(self, attr_name) + 1
        object.__setattr__(self, attr_name, new_value)

        # Increment total
        object.__setattr__(self, "total_decisions", self.total_decisions + 1)

        # Recompute approval_rate
        if self.total_decisions > 0:
            object.__setattr__(
                self, "approval_rate", self.approved_count / self.total_decisions
            )

        # Update keyword stats
        if keywords:
            is_approved = decision_type == "approved"
            for kw in keywords:
                existing = self.keywords.get(kw)
                if existing:
                    new_count = existing.count + 1
                    new_approved = existing.approved_count + (1 if is_approved else 0)
                    new_stat = KeywordStat(
                        keyword=kw,
                        count=new_count,
                        approved_count=new_approved,
                    )
                else:
                    new_stat = KeywordStat(
                        keyword=kw,
                        count=1,
                        approved_count=1 if is_approved else 0,
                    )
                new_keywords = dict(self.keywords)
                new_keywords[kw] = new_stat
                object.__setattr__(self, "keywords", new_keywords)

        object.__setattr__(self, "last_updated", datetime.now(timezone.utc))
