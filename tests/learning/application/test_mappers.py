"""Tests for all Mappers — 7 mappers, domain entity → DTO conversion."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from learning.application.dto.source_dto import KeywordStatDTO
from learning.application.dto.source_dto import SourceQualityDTO as SourceQualityDTODto
from learning.application.mappers import (
    AnalyticsMapper,
    DatasetMapper,
    FeedbackMapper,
    FeatureSnapshotMapper,
    LearningModelMapper,
    LearningSignalMapper,
    SourceQualityMapper,
)
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import FeedbackId, LearningSignalId
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.keyword_stat_vo import KeywordStat

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


# ── FeedbackMapper Tests ──


class TestFeedbackMapper:
    """FeedbackMapper → FeedbackRecord → FeedbackSummaryDTO / FeedbackDetailDTO."""

    def test_to_summary_maps_all_fields(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        dto = FeedbackMapper.to_summary(feedback_record)
        assert dto.id == "00000000-0000-0000-0000-000000000001"
        assert dto.topic_id == "topic-ai"
        assert dto.decision == "APPROVED"
        assert dto.source_name == "TechBlog"
        assert dto.created_at == FIXED_TS.isoformat()

    def test_to_summary_returns_summary_dto_type(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        from learning.application.dto.feedback_dto import FeedbackSummaryDTO
        dto = FeedbackMapper.to_summary(feedback_record)
        assert isinstance(dto, FeedbackSummaryDTO)

    def test_to_summary_id_is_str(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        dto = FeedbackMapper.to_summary(feedback_record)
        assert isinstance(dto.id, str)

    def test_to_summary_decision_is_enum_value(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        dto = FeedbackMapper.to_summary(feedback_record)
        assert dto.decision == DecisionType.APPROVED.value

    def test_to_detail_maps_all_fields(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        dto = FeedbackMapper.to_detail(feedback_record)
        assert dto.id == "00000000-0000-0000-0000-000000000001"
        assert dto.topic_id == "topic-ai"
        assert dto.decision == "APPROVED"
        assert dto.reason is None
        assert dto.source_name == "TechBlog"
        assert dto.title == "Why Python Is Great"
        assert dto.created_at == FIXED_TS.isoformat()

    def test_to_detail_maps_feature_snapshot_to_dict(
        self, feedback_record: FeedbackRecord,
    ) -> None:
        dto = FeedbackMapper.to_detail(feedback_record)
        assert dto.features is not None
        assert isinstance(dto.features, dict)
        assert dto.features["base_score"] == 0.75
        assert dto.features["freshness_score"] == 0.80
        assert dto.features["keyword_bonus"] == 0.60
        assert dto.features["source_bonus"] == 0.55
        assert dto.features["topic_penalty"] == 0.10
        assert dto.features["confidence"] == 0.90
        assert dto.features["final_score"] == 0.82
        # timestamp is NOT included in features dict
        assert "timestamp" not in dto.features

    def test_to_detail_with_rejection_reason(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        record = FeedbackRecord(
            id=FeedbackId.from_string("00000000-0000-0000-0000-000000000099"),
            topic_id="topic-ai",
            decision=DecisionType.REJECTED,
            reason="Off-topic content",
            feature_snapshot=feature_snapshot,
            source_name="SpamBlog",
            title="Buy Now!!!",
            captured_at=FIXED_TS,
        )
        dto = FeedbackMapper.to_detail(record)
        assert dto.reason == "Off-topic content"
        assert dto.decision == "REJECTED"

    def test_to_summary_with_rejection_decision(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        record = FeedbackRecord(
            id=FeedbackId.from_string("00000000-0000-0000-0000-000000000088"),
            topic_id="topic-ai",
            decision=DecisionType.OVERRIDDEN,
            reason="Human override",
            feature_snapshot=feature_snapshot,
            source_name="TestSource",
            title="Test Title",
            captured_at=FIXED_TS,
        )
        dto = FeedbackMapper.to_summary(record)
        assert dto.decision == "OVERRIDDEN"


# ── LearningSignalMapper Tests ──


class TestLearningSignalMapper:
    """LearningSignalMapper → LearningSignal → LearningSignalDTO."""

    def test_to_dto_maps_all_fields(
        self, learning_signal: LearningSignal,
    ) -> None:
        dto = LearningSignalMapper.to_dto(learning_signal)
        assert dto.id == "00000000-0000-0000-0000-000000000002"
        assert dto.dimension == "KEYWORD"  # signal_type.value
        assert dto.source == "python"  # dimension
        assert dto.sample_size == 42
        assert dto.approval_rate == 0.78
        assert dto.strength == 0.85  # strength.value
        assert dto.decay_factor == 0.1  # strength.decay_factor
        assert dto.updated_at == FIXED_TS.isoformat()

    def test_to_dto_returns_correct_type(
        self, learning_signal: LearningSignal,
    ) -> None:
        from learning.application.dto.signal_dto import LearningSignalDTO
        dto = LearningSignalMapper.to_dto(learning_signal)
        assert isinstance(dto, LearningSignalDTO)

    def test_to_dto_dimension_is_signal_type_value(
        self, learning_signal: LearningSignal,
    ) -> None:
        """Verify dimension in DTO comes from signal_type.value (not entity.dimension)."""
        from learning.domain.value_objects.signal_type import SignalType
        assert learning_signal.signal_type == SignalType.KEYWORD
        dto = LearningSignalMapper.to_dto(learning_signal)
        assert dto.dimension == "KEYWORD"

    def test_to_dto_source_is_entity_dimension(
        self, learning_signal: LearningSignal,
    ) -> None:
        """Verify source in DTO comes from entity.dimension (the keyword text)."""
        dto = LearningSignalMapper.to_dto(learning_signal)
        assert dto.source == "python"


# ── SourceQualityMapper Tests ──


class TestSourceQualityMapper:
    """SourceQualityMapper → SourceQualityProfile → SourceQualityDTO."""

    def test_to_dto_maps_all_fields(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        dto = SourceQualityMapper.to_dto(source_quality)
        assert dto.source_name == "TechBlog"
        assert dto.total_decisions == 20
        assert dto.approved == 15
        assert dto.rejected == 3
        assert dto.overridden == 1
        assert dto.approval_rate == 0.75  # 15 / 20

    def test_to_dto_keyword_stats_are_tuple(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        dto = SourceQualityMapper.to_dto(source_quality)
        assert isinstance(dto.keyword_stats, tuple)
        assert len(dto.keyword_stats) == 2

    def test_to_dto_keyword_stats_are_keyword_stat_dto(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        dto = SourceQualityMapper.to_dto(source_quality)
        for stat in dto.keyword_stats:
            assert isinstance(stat, KeywordStatDTO)

    def test_to_dto_keyword_stat_fields_mapped(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        dto = SourceQualityMapper.to_dto(source_quality)
        kw_dict = {s.keyword: s for s in dto.keyword_stats}
        assert "python" in kw_dict
        assert kw_dict["python"].count == 10
        assert kw_dict["python"].approved_count == 8
        assert kw_dict["python"].approval_rate == pytest.approx(0.8)

    def test_to_dto_empty_keywords(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        """Profile with no keywords → empty tuple."""
        profile = SourceQualityProfile(
            id=source_quality.id,
            source_name="EmptySource",
            total_decisions=5,
            approved_count=3,
            rejected_count=2,
        )
        dto = SourceQualityMapper.to_dto(profile)
        assert dto.keyword_stats == ()

    def test_to_dto_returns_correct_type(
        self, source_quality: SourceQualityProfile,
    ) -> None:
        dto = SourceQualityMapper.to_dto(source_quality)
        assert isinstance(dto, SourceQualityDTODto)


# ── LearningModelMapper Tests ──


class TestLearningModelMapper:
    """LearningModelMapper → LearningModel → LearningModelDTO."""

    def test_to_dto_maps_all_fields(
        self, learning_model: LearningModel,
    ) -> None:
        dto = LearningModelMapper.to_dto(learning_model)
        assert dto.id == "00000000-0000-0000-0000-000000000004"
        assert dto.algorithm_version == "1.2.3"
        assert dto.minimum_confidence == 0.5
        assert dto.minimum_sample_size == 10
        assert dto.rules_count == 2

    def test_to_dto_weights_is_dict(
        self, learning_model: LearningModel,
    ) -> None:
        dto = LearningModelMapper.to_dto(learning_model)
        assert isinstance(dto.weights, dict)
        assert dto.weights["relevance"] == 0.30
        assert dto.weights["popularity"] == 0.25
        assert dto.weights["recency"] == 0.20
        assert dto.weights["source_reliability"] == 0.25

    def test_to_dto_algorithm_version_is_str(
        self, learning_model: LearningModel,
    ) -> None:
        dto = LearningModelMapper.to_dto(learning_model)
        assert isinstance(dto.algorithm_version, str)
        assert dto.algorithm_version == "1.2.3"

    def test_to_dto_rules_count_matches_active_rules(
        self, learning_model: LearningModel,
    ) -> None:
        dto = LearningModelMapper.to_dto(learning_model)
        assert dto.rules_count == len(learning_model.active_rules)

    def test_to_dto_empty_rules(
        self, learning_model: LearningModel,
    ) -> None:
        """Model with no active rules → rules_count = 0."""
        from learning.domain.value_objects.algorithm_version import AlgorithmVersion
        from learning.domain.value_objects.score_weights import ScoreWeights
        from learning.domain.entities.ids import LearningModelId

        model = LearningModel(
            id=LearningModelId.from_string("00000000-0000-0000-0000-000000000005"),
            algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
            current_weights=ScoreWeights(
                relevance=0.25, popularity=0.25, recency=0.25, source_reliability=0.25,
            ),
            active_rules=[],
        )
        dto = LearningModelMapper.to_dto(model)
        assert dto.rules_count == 0


# ── FeatureSnapshotMapper Tests ──


class TestFeatureSnapshotMapper:
    """FeatureSnapshotMapper → FeatureSnapshot → ExplanationDTO."""

    def test_to_dto_maps_all_scoring_fields(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        dto = FeatureSnapshotMapper.to_dto(
            snapshot=feature_snapshot,
            source_name="TechBlog",
            model_version="1.2.3",
            active_signals=("KEYWORD:python",),
        )
        assert dto.base_score == 0.75
        assert dto.freshness_score == 0.80
        assert dto.keyword_bonus == 0.60
        assert dto.source_bonus == 0.55
        assert dto.topic_penalty == 0.10
        assert dto.confidence == 0.90
        assert dto.final_score == 0.82

    def test_to_dto_maps_metadata_fields(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        dto = FeatureSnapshotMapper.to_dto(
            snapshot=feature_snapshot,
            source_name="TechBlog",
            model_version="1.2.3",
            active_signals=("KEYWORD:python", "SOURCE:TechBlog"),
        )
        assert dto.source_name == "TechBlog"
        assert dto.model_version == "1.2.3"
        assert dto.active_signals == ("KEYWORD:python", "SOURCE:TechBlog")

    def test_to_dto_timestamp_is_isoformat(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        dto = FeatureSnapshotMapper.to_dto(
            snapshot=feature_snapshot,
            source_name="s",
            model_version="1.0.0",
            active_signals=(),
        )
        assert dto.timestamp == FIXED_TS.isoformat()

    def test_to_dto_empty_active_signals(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        dto = FeatureSnapshotMapper.to_dto(
            snapshot=feature_snapshot,
            source_name="s",
            model_version="1.0.0",
            active_signals=(),
        )
        assert dto.active_signals == ()

    def test_to_dto_returns_explanation_dto_type(
        self, feature_snapshot: FeatureSnapshot,
    ) -> None:
        from learning.application.dto.explanation_dto import ExplanationDTO
        dto = FeatureSnapshotMapper.to_dto(
            snapshot=feature_snapshot,
            source_name="s",
            model_version="1.0.0",
            active_signals=(),
        )
        assert isinstance(dto, ExplanationDTO)


# ── AnalyticsMapper Tests ──


class TestAnalyticsMapper:
    """AnalyticsMapper → aggregated data → AnalyticsDTO."""

    def test_to_dto_maps_all_fields(self) -> None:
        top = SourceQualityDTODto(
            source_name="Blog", total_decisions=10, approved=8,
            rejected=2, overridden=0, approval_rate=0.8,
        )
        dto = AnalyticsMapper.to_dto(
            feedback_count=100,
            signal_count=50,
            avg_rate=0.72,
            signals_by_dim={"KEYWORD": 30, "SOURCE": 20},
            top_sources=(top,),
        )
        assert dto.total_feedback == 100
        assert dto.total_signals == 50
        assert dto.average_approval_rate == 0.72
        assert dto.signals_by_dimension == {"KEYWORD": 30, "SOURCE": 20}
        assert len(dto.top_sources) == 1

    def test_to_dto_empty_data(self) -> None:
        dto = AnalyticsMapper.to_dto(
            feedback_count=0,
            signal_count=0,
            avg_rate=0.0,
            signals_by_dim={},
            top_sources=(),
        )
        assert dto.total_feedback == 0
        assert dto.signals_by_dimension == {}
        assert dto.top_sources == ()

    def test_to_dto_returns_analytics_dto_type(self) -> None:
        from learning.application.dto.analytics_dto import AnalyticsDTO
        dto = AnalyticsMapper.to_dto(
            feedback_count=0, signal_count=0, avg_rate=0.0,
            signals_by_dim={}, top_sources=(),
        )
        assert isinstance(dto, AnalyticsDTO)

    def test_to_dto_top_sources_are_tuple(self) -> None:
        dto = AnalyticsMapper.to_dto(
            feedback_count=0, signal_count=0, avg_rate=0.0,
            signals_by_dim={}, top_sources=(),
        )
        assert isinstance(dto.top_sources, tuple)


# ── DatasetMapper Tests ──


class TestDatasetMapper:
    """DatasetMapper → Dataset entity → DatasetDTO."""

    def _make_dataset_entity(self) -> SimpleNamespace:
        """Create a mock Dataset entity (domain entity TBD)."""
        return SimpleNamespace(
            id="ds-1",
            name="Training Set v1",
            time_window_start="2026-01-01T00:00:00Z",
            time_window_end="2026-07-01T00:00:00Z",
            sample_count=500,
            created_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )

    def test_to_dto_maps_all_fields(self) -> None:
        entity = self._make_dataset_entity()
        dto = DatasetMapper.to_dto(entity)
        assert dto.id == "ds-1"
        assert dto.name == "Training Set v1"
        assert dto.time_window_start == "2026-01-01T00:00:00Z"
        assert dto.time_window_end == "2026-07-01T00:00:00Z"
        assert dto.sample_count == 500
        assert dto.created_at == datetime(2026, 7, 15, tzinfo=timezone.utc).isoformat()

    def test_to_dto_id_is_str(self) -> None:
        entity = self._make_dataset_entity()
        dto = DatasetMapper.to_dto(entity)
        assert isinstance(dto.id, str)

    def test_to_dto_created_at_is_isoformat(self) -> None:
        entity = self._make_dataset_entity()
        dto = DatasetMapper.to_dto(entity)
        assert isinstance(dto.created_at, str)

    def test_to_dto_returns_dataset_dto_type(self) -> None:
        from learning.application.dto.dataset_dto import DatasetDTO
        entity = self._make_dataset_entity()
        dto = DatasetMapper.to_dto(entity)
        assert isinstance(dto, DatasetDTO)
