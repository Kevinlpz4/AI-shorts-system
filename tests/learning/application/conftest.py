"""
Test fixtures for Learning Application Layer tests.

Provides real domain entities for mapper tests and shared fixtures.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is on sys.path for learning.application imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

import pytest

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
from learning.domain.value_objects.keyword_stat_vo import KeywordStat
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow

# ── Fixed timestamp for deterministic tests ──
FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


@pytest.fixture()
def feature_snapshot() -> FeatureSnapshot:
    """A real FeatureSnapshot with all 7 scoring fields."""
    return FeatureSnapshot(
        base_score=0.75,
        freshness_score=0.80,
        keyword_bonus=0.60,
        source_bonus=0.55,
        topic_penalty=0.10,
        confidence=0.90,
        final_score=0.82,
        timestamp=FIXED_TS,
    )


@pytest.fixture()
def feedback_record(feature_snapshot: FeatureSnapshot) -> FeedbackRecord:
    """A real FeedbackRecord with all required fields."""
    return FeedbackRecord(
        id=FeedbackId.from_string("00000000-0000-0000-0000-000000000001"),
        topic_id="topic-ai",
        decision=DecisionType.APPROVED,
        reason=None,
        feature_snapshot=feature_snapshot,
        source_name="TechBlog",
        title="Why Python Is Great",
        score_snapshot={"relevance": 0.8},
        captured_at=FIXED_TS,
    )


@pytest.fixture()
def learning_signal() -> LearningSignal:
    """A real LearningSignal with all required fields."""
    return LearningSignal(
        id=LearningSignalId.from_string("00000000-0000-0000-0000-000000000002"),
        signal_type=SignalType.KEYWORD,
        dimension="python",
        strength=SignalStrength(value=0.85, decay_factor=0.1),
        sample_size=42,
        approval_rate=0.78,
        window=TimeWindow(
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 7, 15, tzinfo=timezone.utc),
        ),
        last_updated=FIXED_TS,
    )


@pytest.fixture()
def source_quality() -> SourceQualityProfile:
    """A real SourceQualityProfile with keyword stats."""
    return SourceQualityProfile(
        id=SourceQualityId.from_string("00000000-0000-0000-0000-000000000003"),
        source_name="TechBlog",
        total_decisions=20,
        approved_count=15,
        rejected_count=3,
        auto_approved_count=1,
        auto_rejected_count=0,
        overridden_count=1,
        keywords={
            "python": KeywordStat(keyword="python", count=10, approved_count=8),
            "rust": KeywordStat(keyword="rust", count=5, approved_count=4),
        },
        last_updated=FIXED_TS,
    )


@pytest.fixture()
def learning_model() -> LearningModel:
    """A real LearningModel with all required fields."""
    return LearningModel(
        id=LearningModelId.from_string("00000000-0000-0000-0000-000000000004"),
        algorithm_version=AlgorithmVersion(major=1, minor=2, patch=3),
        current_weights=ScoreWeights(
            relevance=0.30,
            popularity=0.25,
            recency=0.20,
            source_reliability=0.25,
        ),
        minimum_confidence=0.5,
        minimum_sample_size=10,
        active_rules=["keyword_boost", "source_penalty"],
        created_at=FIXED_TS,
        updated_at=FIXED_TS,
    )
