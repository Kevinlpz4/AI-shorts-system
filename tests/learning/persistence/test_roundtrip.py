"""
Full roundtrip tests — domain -> model -> domain for all entities.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.domain.entities.ids import (
    FeedbackId,
    LearningSignalId,
    SourceQualityId,
    LearningModelId,
    KnowledgeArtifactId,
)
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.knowledge_artifact import ArtifactStatus, ArtifactType, KnowledgeArtifact
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.keyword_stat_vo import KeywordStat

from learning.persistence.mappers.feedback_mapper import FeedbackRecordMapper
from learning.persistence.mappers.learning_signal_mapper import LearningSignalMapper
from learning.persistence.mappers.source_quality_mapper import SourceQualityMapper
from learning.persistence.mappers.learning_model_mapper import LearningModelMapper
from learning.persistence.mappers.knowledge_artifact_mapper import KnowledgeArtifactMapper

from learning.persistence.models.feedback import FeedbackRecordModel
from learning.persistence.models.learning_signal import LearningSignalModel
from learning.persistence.models.source_quality import SourceQualityProfileModel
from learning.persistence.models.learning_model import LearningModelModel
from learning.persistence.models.knowledge_artifact import KnowledgeArtifactModel


class TestFeedbackRecordRoundtrip:
    def test_full_roundtrip(self):
        now = datetime.now(timezone.utc)
        feature = FeatureSnapshot(
            base_score=0.75,
            freshness_score=0.85,
            keyword_bonus=0.3,
            source_bonus=0.5,
            topic_penalty=0.1,
            confidence=0.9,
            final_score=0.65,
            timestamp=now,
        )
        fid = FeedbackId.generate()
        entity = FeedbackRecord(
            id=fid,
            topic_id="topic-42",
            decision=DecisionType.APPROVED,
            reason=None,
            feature_snapshot=feature,
            source_name="bbc-news",
            title="Test Article",
            score_snapshot={"relevance": 0.8, "popularity": 0.2},
            captured_at=now,
        )

        # Domain -> Model
        model = FeedbackRecordMapper.to_model(entity)
        assert model.id == str(fid)
        assert model.decision == "APPROVED"
        assert model.source_name == "bbc-news"

        # Model -> Domain
        restored = FeedbackRecordMapper.to_domain(model)
        assert restored.id == fid
        assert restored.topic_id == "topic-42"
        assert restored.decision == DecisionType.APPROVED
        assert restored.reason is None
        assert restored.feature_snapshot.base_score == 0.75
        assert restored.feature_snapshot.timestamp == now
        assert restored.source_name == "bbc-news"
        assert restored.title == "Test Article"
        assert restored.score_snapshot == {"relevance": 0.8, "popularity": 0.2}

    def test_roundtrip_with_rejection(self):
        now = datetime.now(timezone.utc)
        feature = FeatureSnapshot(
            base_score=0.3,
            freshness_score=0.5,
            keyword_bonus=0.1,
            source_bonus=0.2,
            topic_penalty=0.8,
            confidence=0.4,
            final_score=0.25,
            timestamp=now,
        )
        fid = FeedbackId.generate()
        entity = FeedbackRecord(
            id=fid,
            topic_id="topic-99",
            decision=DecisionType.REJECTED,
            reason="Low quality content",
            feature_snapshot=feature,
            source_name="clickbait-site",
            title="You Won't Believe This",
            score_snapshot={},
            captured_at=now,
        )

        model = FeedbackRecordMapper.to_model(entity)
        restored = FeedbackRecordMapper.to_domain(model)
        assert restored.decision == DecisionType.REJECTED
        assert restored.reason == "Low quality content"


class TestLearningSignalRoundtrip:
    def test_full_roundtrip(self):
        now = datetime.now(timezone.utc)
        fid = LearningSignalId.generate()
        entity = LearningSignal(
            id=fid,
            signal_type=SignalType.KEYWORD,
            dimension="python",
            strength=SignalStrength(value=0.85, decay_factor=0.15),
            sample_size=42,
            approval_rate=0.78,
            window=TimeWindow(
                start=now - timedelta(days=30),
                end=now,
            ),
            last_updated=now,
        )

        model = LearningSignalMapper.to_model(entity)
        restored = LearningSignalMapper.to_domain(model)

        assert restored.id == fid
        assert restored.signal_type == SignalType.KEYWORD
        assert restored.dimension == "python"
        assert restored.strength.value == 0.85
        assert restored.strength.decay_factor == 0.15
        assert restored.sample_size == 42
        assert restored.approval_rate == 0.78


class TestSourceQualityRoundtrip:
    def test_full_roundtrip(self):
        now = datetime.now(timezone.utc)
        fid = SourceQualityId.generate()
        keywords = {
            "python": KeywordStat(keyword="python", count=10, approved_count=8),
            "java": KeywordStat(keyword="java", count=5, approved_count=3),
        }
        entity = SourceQualityProfile(
            id=fid,
            source_name="tech-blog",
            total_decisions=20,
            approved_count=15,
            rejected_count=3,
            auto_approved_count=1,
            auto_rejected_count=1,
            overridden_count=0,
            keywords=keywords,
            last_updated=now,
        )

        model = SourceQualityMapper.to_model(entity)
        restored = SourceQualityMapper.to_domain(model)

        assert restored.id == fid
        assert restored.source_name == "tech-blog"
        assert restored.total_decisions == 20
        assert restored.approved_count == 15
        assert restored.approval_rate == 0.75
        assert "python" in restored.keywords
        assert restored.keywords["python"].count == 10
        assert restored.keywords["java"].approved_count == 3

    def test_roundtrip_empty_keywords(self):
        now = datetime.now(timezone.utc)
        entity = SourceQualityProfile(
            id=SourceQualityId.generate(),
            source_name="empty-source",
        )

        model = SourceQualityMapper.to_model(entity)
        restored = SourceQualityMapper.to_domain(model)

        assert restored.keywords == {}
        assert restored.total_decisions == 0
        assert restored.approval_rate == 0.0


class TestLearningModelRoundtrip:
    def test_full_roundtrip(self):
        now = datetime.now(timezone.utc)
        fid = LearningModelId.generate()
        entity = LearningModel(
            id=fid,
            algorithm_version=AlgorithmVersion(major=2, minor=3, patch=1),
            current_weights=ScoreWeights(
                relevance=0.35, popularity=0.25, recency=0.2, source_reliability=0.2
            ),
            minimum_confidence=0.6,
            minimum_sample_size=15,
            active_rules=["keyword_boost", "source_penalty"],
            created_at=now,
            updated_at=now,
        )

        model = LearningModelMapper.to_model(entity)
        restored = LearningModelMapper.to_domain(model)

        assert restored.id == fid
        assert restored.algorithm_version == AlgorithmVersion(major=2, minor=3, patch=1)
        assert restored.current_weights.relevance == 0.35
        assert restored.minimum_confidence == 0.6
        assert restored.minimum_sample_size == 15
        assert restored.active_rules == ["keyword_boost", "source_penalty"]

    def test_roundtrip_empty_rules(self):
        entity = LearningModel(
            id=LearningModelId.generate(),
            algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
            current_weights=ScoreWeights(
                relevance=0.25, popularity=0.25, recency=0.25, source_reliability=0.25
            ),
        )

        model = LearningModelMapper.to_model(entity)
        restored = LearningModelMapper.to_domain(model)

        assert restored.active_rules == []


class TestKnowledgeArtifactRoundtrip:
    def test_full_roundtrip(self):
        now = datetime.now(timezone.utc)
        fid = KnowledgeArtifactId.generate()
        entity = KnowledgeArtifact(
            id=fid,
            artifact_type=ArtifactType.DATASET,
            version="2.1.0",
            created_at=now,
            created_by="training_pipeline",
            source_dataset="ds-42",
            algorithm_version="1.5.0",
            feature_version="2.0.0",
            checksum="sha256:abc123",
            metadata={"batch_size": 32, "epochs": 10},
            status=ArtifactStatus.ACTIVE,
        )

        model = KnowledgeArtifactMapper.to_model(entity)
        restored = KnowledgeArtifactMapper.to_domain(model)

        assert restored.id == fid
        assert restored.artifact_type == ArtifactType.DATASET
        assert restored.version == "2.1.0"
        assert restored.created_by == "training_pipeline"
        assert restored.source_dataset == "ds-42"
        assert restored.checksum == "sha256:abc123"
        assert restored.metadata["batch_size"] == 32
        assert restored.status == ArtifactStatus.ACTIVE
