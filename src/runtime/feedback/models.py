"""
Feedback data models — immutable records and mutable session containers.

Design principles:
    1. FeedbackRecord is frozen — decisions are immutable facts.
    2. DecisionSession is mutable — it accumulates records over time.
    3. Decision enum encodes the three possible human actions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class Decision(Enum):
    """Human decision on a recommended item."""

    APPROVE = "approve"
    REJECT = "reject"
    SKIP = "skip"


@dataclass(frozen=True)
class FeedbackRecord:
    """Immutable record of a human decision on a recommended item.

    This is the core data unit that flows through analytics, persistence,
    and event emission. It captures the full context of a decision including
    algorithm state at decision time.
    """

    id: str
    article_id: str
    provider: str
    source: str
    category: str
    topic: str
    recommended_score: float
    recommendation: str
    decision: Decision
    reason: str
    comment: Optional[str]
    user_id: str
    timestamp: datetime
    algorithm_version: str
    feature_snapshot_version: str
    dataset_version: str


@dataclass
class DecisionSession:
    """Groups decisions made in a single review session.

    Mutable — designed to accumulate records and stats over time.
    """

    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    decisions: List[FeedbackRecord] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
