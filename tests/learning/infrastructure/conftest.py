"""
Test fixtures for Learning Infrastructure tests.

Provides real domain entities for repository, UoW, EventPublisher,
Clock, and DatasetExporter tests.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is on sys.path for learning infrastructure imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# ---------------------------------------------------------------------------
# Domain Entities
# ---------------------------------------------------------------------------
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
)
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow

# ---------------------------------------------------------------------------
# Fixed timestamp used across all tests
# ---------------------------------------------------------------------------
FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# FeedbackRecord fixture
# ---------------------------------------------------------------------------


def make_feedback(
    *,
    id: FeedbackId | None = None,
    topic_id: str = "topic-1",
    decision: DecisionType = DecisionType.APPROVED,
    reason: str | None = None,
    source_name: str = "test-source",
    title: str = "Test Article",
    captured_at: datetime | None = None,
) -> FeedbackRecord:
    """Create a FeedbackRecord with sensible defaults."""
    if decision in (
        DecisionType.REJECTED,
        DecisionType.AUTO_REJECTED,
        DecisionType.OVERRIDDEN,
    ):
        reason = reason or "quality_too_low"

    feature = FeatureSnapshot(
        base_score=0.8,
        freshness_score=0.7,
        keyword_bonus=0.3,
        source_bonus=0.5,
        topic_penalty=0.1,
        confidence=0.9,
        final_score=0.75,
        timestamp=captured_at or FIXED_TS,
    )

    return FeedbackRecord(
        id=id or FeedbackId.generate(),
        topic_id=topic_id,
        decision=decision,
        reason=reason,
        feature_snapshot=feature,
        source_name=source_name,
        title=title,
        score_snapshot={"relevance": 0.8, "popularity": 0.6},
        captured_at=captured_at or FIXED_TS,
    )


# ---------------------------------------------------------------------------
# LearningSignal fixture
# ---------------------------------------------------------------------------


def make_signal(
    *,
    id: LearningSignalId | None = None,
    signal_type: SignalType = SignalType.KEYWORD,
    dimension: str = "python",
    strength_value: float = 0.85,
    sample_size: int = 20,
    approval_rate: float = 0.75,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> LearningSignal:
    """Create a LearningSignal with sensible defaults."""
    ws = window_start or datetime(2026, 7, 1, tzinfo=timezone.utc)
    we = window_end or datetime(2026, 7, 15, tzinfo=timezone.utc)
    return LearningSignal(
        id=id or LearningSignalId.generate(),
        signal_type=signal_type,
        dimension=dimension,
        strength=SignalStrength(value=strength_value, decay_factor=0.1),
        sample_size=sample_size,
        approval_rate=approval_rate,
        window=TimeWindow(start=ws, end=we),
        last_updated=FIXED_TS,
    )


# ---------------------------------------------------------------------------
# SourceQualityProfile fixture
# ---------------------------------------------------------------------------


def make_source_quality(
    *,
    id: SourceQualityId | None = None,
    source_name: str = "test-source",
    total_decisions: int = 10,
    approved_count: int = 7,
    rejected_count: int = 2,
    auto_approved_count: int = 1,
    auto_rejected_count: int = 0,
    overridden_count: int = 0,
) -> SourceQualityProfile:
    """Create a SourceQualityProfile with sensible defaults."""
    return SourceQualityProfile(
        id=id or SourceQualityId.generate(),
        source_name=source_name,
        total_decisions=total_decisions,
        approved_count=approved_count,
        rejected_count=rejected_count,
        auto_approved_count=auto_approved_count,
        auto_rejected_count=auto_rejected_count,
        overridden_count=overridden_count,
        last_updated=FIXED_TS,
    )


# ---------------------------------------------------------------------------
# LearningModel fixture
# ---------------------------------------------------------------------------


def make_model(
    *,
    id: LearningModelId | None = None,
    version: str = "1.0.0",
    minimum_confidence: float = 0.5,
    minimum_sample_size: int = 10,
    active_rules: list[str] | None = None,
) -> LearningModel:
    """Create a LearningModel with sensible defaults."""
    return LearningModel(
        id=id or LearningModelId.generate(),
        algorithm_version=AlgorithmVersion.parse(version),
        current_weights=ScoreWeights(
            relevance=0.3, popularity=0.2, recency=0.25, source_reliability=0.25
        ),
        minimum_confidence=minimum_confidence,
        minimum_sample_size=minimum_sample_size,
        active_rules=active_rules,
        created_at=FIXED_TS,
        updated_at=FIXED_TS,
    )
