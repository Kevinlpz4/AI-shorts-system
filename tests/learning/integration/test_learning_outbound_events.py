"""
Tests for Learning Outbound Events — 4 outbound Integration Events from Learning BC.

Validates: frozen dataclasses, IntegrationEvent inheritance, source_boundary defaults,
event_name property, construction with all fields, and equality semantics.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from foundation.events.integration_event import IntegrationEvent

FIXED_TS = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
from learning.integration.events.learning_outbound_events import (
    DatasetReady,
    FeedbackRecorded,
    LearningSignalUpdated,
    RecommendationGenerated,
)


# ─── RecommendationGenerated ──────────────────────────────────────────

class TestRecommendationGenerated:
    """RecommendationGenerated — Learning generated a recommendation."""

    def _make(self) -> RecommendationGenerated:
        return RecommendationGenerated(
            recommendation="APPROVE",
            probability=0.85,
            confidence=0.92,
            source_name="Reuters",
            reasoning='["high_quality_source", "relevant_keywords"]',
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "learning"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "RecommendationGenerated"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.recommendation == "APPROVE"
        assert event.probability == 0.85
        assert event.confidence == 0.92
        assert event.source_name == "Reuters"
        assert event.reasoning == '["high_quality_source", "relevant_keywords"]'

    def test_construction_defaults(self) -> None:
        event = RecommendationGenerated()
        assert event.recommendation == ""
        assert event.probability == 0.0
        assert event.confidence == 0.0
        assert event.source_name == ""
        assert event.reasoning == ""
        assert event.source_boundary == "learning"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.recommendation = "REJECT"  # type: ignore[misc]

    def test_frozen_probability(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.probability = 0.5  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = RecommendationGenerated(event_id=eid, occurred_at=FIXED_TS, recommendation="APPROVE", probability=0.85)
        b = RecommendationGenerated(event_id=eid, occurred_at=FIXED_TS, recommendation="APPROVE", probability=0.85)
        assert a == b

    def test_inequality_different_id(self) -> None:
        a = RecommendationGenerated(recommendation="APPROVE")
        b = RecommendationGenerated(recommendation="APPROVE")
        assert a != b

    def test_inequality_different_data(self) -> None:
        eid = uuid4()
        a = RecommendationGenerated(event_id=eid, recommendation="APPROVE")
        b = RecommendationGenerated(event_id=eid, recommendation="REJECT")
        assert a != b


# ─── FeedbackRecorded ─────────────────────────────────────────────────

class TestFeedbackRecorded:
    """FeedbackRecorded — Learning recorded a feedback decision."""

    def _make(self) -> FeedbackRecorded:
        return FeedbackRecorded(
            feedback_id="fb-001",
            topic_id="topic-ai",
            decision="approved",
            source_name="TechBlog",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "learning"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "FeedbackRecorded"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.feedback_id == "fb-001"
        assert event.topic_id == "topic-ai"
        assert event.decision == "approved"
        assert event.source_name == "TechBlog"

    def test_construction_defaults(self) -> None:
        event = FeedbackRecorded()
        assert event.feedback_id == ""
        assert event.topic_id == ""
        assert event.decision == ""
        assert event.source_name == ""
        assert event.source_boundary == "learning"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.decision = "rejected"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = FeedbackRecorded(event_id=eid, occurred_at=FIXED_TS, feedback_id="fb-001", decision="approved")
        b = FeedbackRecorded(event_id=eid, occurred_at=FIXED_TS, feedback_id="fb-001", decision="approved")
        assert a == b

    def test_inequality(self) -> None:
        a = FeedbackRecorded(feedback_id="fb-001")
        b = FeedbackRecorded(feedback_id="fb-002")
        assert a != b


# ─── LearningSignalUpdated ────────────────────────────────────────────

class TestLearningSignalUpdated:
    """LearningSignalUpdated — Learning updated a signal."""

    def _make(self) -> LearningSignalUpdated:
        return LearningSignalUpdated(
            signal_id="sig-001",
            signal_type="KEYWORD",
            dimension="python",
            strength_value=0.85,
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "learning"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "LearningSignalUpdated"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.signal_id == "sig-001"
        assert event.signal_type == "KEYWORD"
        assert event.dimension == "python"
        assert event.strength_value == 0.85

    def test_construction_defaults(self) -> None:
        event = LearningSignalUpdated()
        assert event.signal_id == ""
        assert event.signal_type == ""
        assert event.dimension == ""
        assert event.strength_value == 0.0
        assert event.source_boundary == "learning"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.strength_value = 0.5  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = LearningSignalUpdated(event_id=eid, occurred_at=FIXED_TS, signal_id="sig-001", strength_value=0.85)
        b = LearningSignalUpdated(event_id=eid, occurred_at=FIXED_TS, signal_id="sig-001", strength_value=0.85)
        assert a == b

    def test_inequality(self) -> None:
        a = LearningSignalUpdated(signal_id="sig-001")
        b = LearningSignalUpdated(signal_id="sig-002")
        assert a != b


# ─── DatasetReady ─────────────────────────────────────────────────────

class TestDatasetReady:
    """DatasetReady — Learning generated a dataset."""

    def _make(self) -> DatasetReady:
        return DatasetReady(
            dataset_id="ds-001",
            record_count=1500,
            format="jsonl",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "learning"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "DatasetReady"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.dataset_id == "ds-001"
        assert event.record_count == 1500
        assert event.format == "jsonl"

    def test_construction_defaults(self) -> None:
        event = DatasetReady()
        assert event.dataset_id == ""
        assert event.record_count == 0
        assert event.format == ""
        assert event.source_boundary == "learning"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.record_count = 999  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = DatasetReady(event_id=eid, occurred_at=FIXED_TS, dataset_id="ds-001", record_count=1500)
        b = DatasetReady(event_id=eid, occurred_at=FIXED_TS, dataset_id="ds-001", record_count=1500)
        assert a == b

    def test_inequality(self) -> None:
        a = DatasetReady(dataset_id="ds-001")
        b = DatasetReady(dataset_id="ds-002")
        assert a != b
