"""Tests for Domain Events — all 5 events from Foundation DomainEvent."""
import pytest
from datetime import datetime, timezone
from foundation.events.domain_event import DomainEvent
from learning.domain.events.learning_events import (
    FeedbackCaptured,
    SignalAggregated,
    ScoreAdjusted,
    DatasetGenerated,
    LearningModelUpdated,
)
from learning.domain.entities.ids import FeedbackId, LearningSignalId, LearningModelId
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.time_window import TimeWindow


NOW = datetime(2026, 7, 15, tzinfo=timezone.utc)
DEFAULT_WEIGHTS = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
DEFAULT_WINDOW = TimeWindow(start=NOW, end=NOW.replace(hour=23))


class TestDomainEvents:
    def test_all_inherit_domain_event(self):
        for cls in (FeedbackCaptured, SignalAggregated, ScoreAdjusted, DatasetGenerated, LearningModelUpdated):
            assert issubclass(cls, DomainEvent)

    def test_feedback_captured(self):
        ev = FeedbackCaptured(
            feedback_id=FeedbackId.generate(),
            topic_id="t-1",
            decision=DecisionType.APPROVED,
            source_name="reddit",
            captured_at=NOW,
        )
        assert ev.topic_id == "t-1"
        assert ev.decision == DecisionType.APPROVED

    def test_feedback_captured_requires_fields(self):
        with pytest.raises(TypeError, match="feedback_id is required"):
            FeedbackCaptured()  # type: ignore[call-arg]

    def test_signal_aggregated(self):
        ev = SignalAggregated(
            signal_id=LearningSignalId.generate(),
            signal_type="KEYWORD",
            dimension="python",
            strength_value=0.8,
            window=DEFAULT_WINDOW,
        )
        assert ev.dimension == "python"
        assert ev.strength_value == 0.8

    def test_signal_aggregated_requires_fields(self):
        with pytest.raises(TypeError, match="signal_id is required"):
            SignalAggregated()  # type: ignore[call-arg]

    def test_score_adjusted(self):
        ev = ScoreAdjusted(
            model_id=LearningModelId.generate(),
            old_weights=DEFAULT_WEIGHTS,
            new_weights=DEFAULT_WEIGHTS,
            reason="Initial calibration",
            adjusted_at=NOW,
        )
        assert ev.reason == "Initial calibration"

    def test_score_adjusted_requires_fields(self):
        with pytest.raises(TypeError, match="model_id is required"):
            ScoreAdjusted()  # type: ignore[call-arg]

    def test_dataset_generated(self):
        ev = DatasetGenerated(
            dataset_id="ds-001",
            version="v1",
            record_count=100,
            format="jsonl",
            generated_at=NOW,
        )
        assert ev.record_count == 100

    def test_dataset_generated_requires_fields(self):
        with pytest.raises(TypeError, match="dataset_id is required"):
            DatasetGenerated()  # type: ignore[call-arg]

    def test_dataset_generated_rejects_negative_count(self):
        with pytest.raises(ValueError, match=">= 0"):
            DatasetGenerated(
                dataset_id="ds-001",
                version="v1",
                record_count=-1,
                format="jsonl",
                generated_at=NOW,
            )

    def test_learning_model_updated(self):
        ev = LearningModelUpdated(
            model_id=LearningModelId.generate(),
            old_version="1.0.0",
            new_version="1.1.0",
            updated_at=NOW,
        )
        assert ev.old_version == "1.0.0"
        assert ev.new_version == "1.1.0"

    def test_learning_model_updated_requires_fields(self):
        with pytest.raises(TypeError, match="model_id is required"):
            LearningModelUpdated()  # type: ignore[call-arg]

    def test_events_are_frozen(self):
        ev = FeedbackCaptured(
            feedback_id=FeedbackId.generate(),
            topic_id="t-1",
            decision=DecisionType.APPROVED,
            source_name="reddit",
            captured_at=NOW,
        )
        with pytest.raises(AttributeError):
            ev.topic_id = "hacked"  # type: ignore[misc]
