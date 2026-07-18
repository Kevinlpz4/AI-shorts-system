"""
Tests for InMemoryTypedEventPublisher.

Covers typed event publishing for each event kind:
FeedbackCaptured, SignalAggregated, ScoreAdjusted,
DatasetGenerated, LearningModelUpdated.
"""
from __future__ import annotations

from datetime import datetime, timezone

from learning.domain.entities.ids import FeedbackId, LearningModelId, LearningSignalId
from learning.domain.events.learning_events import (
    DatasetGenerated,
    FeedbackCaptured,
    LearningModelUpdated,
    ScoreAdjusted,
    SignalAggregated,
)
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.time_window import TimeWindow
from learning.infrastructure.inmemory.learning_event_publisher import (
    InMemoryTypedEventPublisher,
)

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


def _make_feedback_event() -> FeedbackCaptured:
    return FeedbackCaptured(
        feedback_id=FeedbackId.generate(),
        topic_id="topic-1",
        decision=DecisionType.APPROVED,
        source_name="test-source",
        captured_at=FIXED_TS,
    )


def _make_signal_event() -> SignalAggregated:
    return SignalAggregated(
        signal_id=LearningSignalId.generate(),
        signal_type="KEYWORD",
        dimension="python",
        strength_value=0.85,
        window=TimeWindow(
            start=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end=datetime(2026, 7, 15, tzinfo=timezone.utc),
        ),
    )


def _make_score_event() -> ScoreAdjusted:
    old_w = ScoreWeights(
        relevance=0.3, popularity=0.2, recency=0.25, source_reliability=0.25
    )
    new_w = ScoreWeights(
        relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
    )
    return ScoreAdjusted(
        model_id=LearningModelId.generate(),
        old_weights=old_w,
        new_weights=new_w,
        reason="new_feedback_data",
        adjusted_at=FIXED_TS,
    )


def _make_dataset_event() -> DatasetGenerated:
    return DatasetGenerated(
        dataset_id="ds-001",
        version="1.0",
        record_count=100,
        format="json",
        generated_at=FIXED_TS,
    )


def _make_model_event() -> LearningModelUpdated:
    return LearningModelUpdated(
        model_id=LearningModelId.generate(),
        old_version="1.0.0",
        new_version="1.1.0",
        updated_at=FIXED_TS,
    )


class TestInMemoryTypedEventPublisher:
    """Tests for InMemoryTypedEventPublisher."""

    def test_publish_feedback_captured(self) -> None:
        pub = InMemoryTypedEventPublisher()
        event = _make_feedback_event()

        pub.publish_feedback_captured(event)

        assert len(pub.feedback_events) == 1
        assert pub.feedback_events[0] is event
        assert pub.has_feedback_events() is True

    def test_publish_signal_aggregated(self) -> None:
        pub = InMemoryTypedEventPublisher()
        event = _make_signal_event()

        pub.publish_signal_aggregated(event)

        assert len(pub.signal_events) == 1
        assert pub.signal_events[0] is event
        assert pub.has_signal_events() is True

    def test_publish_score_adjusted(self) -> None:
        pub = InMemoryTypedEventPublisher()
        event = _make_score_event()

        pub.publish_score_adjusted(event)

        assert len(pub.score_events) == 1
        assert pub.score_events[0] is event
        assert pub.has_score_events() is True

    def test_publish_dataset_generated(self) -> None:
        pub = InMemoryTypedEventPublisher()
        event = _make_dataset_event()

        pub.publish_dataset_generated(event)

        assert len(pub.dataset_events) == 1
        assert pub.dataset_events[0] is event
        assert pub.has_dataset_events() is True

    def test_publish_learning_model_updated(self) -> None:
        pub = InMemoryTypedEventPublisher()
        event = _make_model_event()

        pub.publish_learning_model_updated(event)

        assert len(pub.model_events) == 1
        assert pub.model_events[0] is event
        assert pub.has_model_events() is True

    def test_has_feedback_events(self) -> None:
        pub = InMemoryTypedEventPublisher()
        assert pub.has_feedback_events() is False

        pub.publish_feedback_captured(_make_feedback_event())
        assert pub.has_feedback_events() is True

    def test_clear(self) -> None:
        pub = InMemoryTypedEventPublisher()
        pub.publish_feedback_captured(_make_feedback_event())
        pub.publish_signal_aggregated(_make_signal_event())
        pub.publish_score_adjusted(_make_score_event())
        pub.publish_dataset_generated(_make_dataset_event())
        pub.publish_learning_model_updated(_make_model_event())

        pub.clear()

        assert len(pub.feedback_events) == 0
        assert len(pub.signal_events) == 0
        assert len(pub.score_events) == 0
        assert len(pub.dataset_events) == 0
        assert len(pub.model_events) == 0
        assert pub.has_feedback_events() is False
        assert pub.has_signal_events() is False
        assert pub.has_score_events() is False
        assert pub.has_dataset_events() is False
        assert pub.has_model_events() is False

    def test_properties_return_copies(self) -> None:
        """Each typed list property returns a copy, not the internal list."""
        pub = InMemoryTypedEventPublisher()
        pub.publish_feedback_captured(_make_feedback_event())

        events1 = pub.feedback_events
        events2 = pub.feedback_events

        assert events1 is not events2
        assert events1 == events2
