"""
Test fixtures for Learning BC persistence tests.

Provides in-memory SQLite session, factories for domain entities,
and shared test data.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from learning.persistence.models.base import Base
from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
    KnowledgeArtifactId,
)
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.knowledge_artifact import (
    ArtifactStatus,
    ArtifactType,
    KnowledgeArtifact,
)
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.keyword_stat_vo import KeywordStat


# ── Session fixtures ──────────────────────────────────────────────────


@pytest.fixture
def engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """SQLAlchemy session bound to the in-memory engine."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def session_factory(engine):
    """Session factory for creating multiple sessions (UnitOfWork tests)."""
    return sessionmaker(bind=engine)


# ── Factory fixtures ──────────────────────────────────────────────────


@pytest.fixture
def make_feature_snapshot():
    """Factory for FeatureSnapshot VOs."""

    def _make(
        base_score: float = 0.7,
        freshness_score: float = 0.8,
        keyword_bonus: float = 0.3,
        source_bonus: float = 0.5,
        topic_penalty: float = 0.1,
        confidence: float = 0.9,
        final_score: float = 0.65,
        timestamp: datetime | None = None,
    ) -> FeatureSnapshot:
        return FeatureSnapshot(
            base_score=base_score,
            freshness_score=freshness_score,
            keyword_bonus=keyword_bonus,
            source_bonus=source_bonus,
            topic_penalty=topic_penalty,
            confidence=confidence,
            final_score=final_score,
            timestamp=timestamp or datetime.now(timezone.utc),
        )

    return _make


@pytest.fixture
def make_feedback_record(make_feature_snapshot):
    """Factory for FeedbackRecord aggregate roots."""

    def _make(
        id: FeedbackId | None = None,
        topic_id: str = "topic-1",
        decision: DecisionType = DecisionType.APPROVED,
        reason: str | None = None,
        feature_snapshot: FeatureSnapshot | None = None,
        source_name: str = "test-source",
        title: str = "Test Title",
        score_snapshot: dict | None = None,
        captured_at: datetime | None = None,
    ) -> FeedbackRecord:
        if decision in (DecisionType.REJECTED, DecisionType.AUTO_REJECTED, DecisionType.OVERRIDDEN):
            reason = reason or "Test rejection reason"
        return FeedbackRecord(
            id=id or FeedbackId.generate(),
            topic_id=topic_id,
            decision=decision,
            reason=reason,
            feature_snapshot=feature_snapshot or make_feature_snapshot(),
            source_name=source_name,
            title=title,
            score_snapshot=score_snapshot or {"relevance": 0.7, "popularity": 0.3},
            captured_at=captured_at,
        )

    return _make


@pytest.fixture
def make_learning_signal():
    """Factory for LearningSignal aggregate roots."""

    def _make(
        id: LearningSignalId | None = None,
        signal_type: SignalType = SignalType.KEYWORD,
        dimension: str = "python",
        strength: SignalStrength | None = None,
        sample_size: int = 10,
        approval_rate: float = 0.8,
        window: TimeWindow | None = None,
        last_updated: datetime | None = None,
    ) -> LearningSignal:
        now = datetime.now(timezone.utc)
        return LearningSignal(
            id=id or LearningSignalId.generate(),
            signal_type=signal_type,
            dimension=dimension,
            strength=strength or SignalStrength(value=0.8, decay_factor=0.1),
            sample_size=sample_size,
            approval_rate=approval_rate,
            window=window or TimeWindow(
                start=now - timedelta(days=30),
                end=now,
            ),
            last_updated=last_updated,
        )

    return _make


@pytest.fixture
def make_source_quality():
    """Factory for SourceQualityProfile aggregate roots."""

    def _make(
        id: SourceQualityId | None = None,
        source_name: str = "test-source",
        total_decisions: int = 10,
        approved_count: int = 8,
        rejected_count: int = 2,
        auto_approved_count: int = 0,
        auto_rejected_count: int = 0,
        overridden_count: int = 0,
        keywords: dict[str, KeywordStat] | None = None,
        last_updated: datetime | None = None,
    ) -> SourceQualityProfile:
        return SourceQualityProfile(
            id=id or SourceQualityId.generate(),
            source_name=source_name,
            total_decisions=total_decisions,
            approved_count=approved_count,
            rejected_count=rejected_count,
            auto_approved_count=auto_approved_count,
            auto_rejected_count=auto_rejected_count,
            overridden_count=overridden_count,
            keywords=keywords or {},
            last_updated=last_updated,
        )

    return _make


@pytest.fixture
def make_learning_model():
    """Factory for LearningModel aggregate roots."""

    def _make(
        id: LearningModelId | None = None,
        algorithm_version: AlgorithmVersion | None = None,
        current_weights: ScoreWeights | None = None,
        minimum_confidence: float = 0.5,
        minimum_sample_size: int = 10,
        active_rules: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> LearningModel:
        return LearningModel(
            id=id or LearningModelId.generate(),
            algorithm_version=algorithm_version or AlgorithmVersion(major=1, minor=0, patch=0),
            current_weights=current_weights or ScoreWeights(
                relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
            ),
            minimum_confidence=minimum_confidence,
            minimum_sample_size=minimum_sample_size,
            active_rules=active_rules,
            created_at=created_at,
            updated_at=updated_at,
        )

    return _make


@pytest.fixture
def make_knowledge_artifact():
    """Factory for KnowledgeArtifact entities."""

    def _make(
        id: KnowledgeArtifactId | None = None,
        artifact_type: ArtifactType = ArtifactType.DATASET,
        version: str = "1.0.0",
        created_at: datetime | None = None,
        created_by: str = "test_user",
        source_dataset: str = "",
        algorithm_version: str = "",
        feature_version: str = "",
        checksum: str = "",
        metadata: dict | None = None,
        status: ArtifactStatus = ArtifactStatus.PENDING,
    ) -> KnowledgeArtifact:
        return KnowledgeArtifact(
            id=id or KnowledgeArtifactId.generate(),
            artifact_type=artifact_type,
            version=version,
            created_at=created_at or datetime.now(timezone.utc),
            created_by=created_by,
            source_dataset=source_dataset,
            algorithm_version=algorithm_version,
            feature_version=feature_version,
            checksum=checksum,
            metadata=metadata or {},
            status=status,
        )

    return _make
