"""
Tests for feedback event emitter.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from runtime.event_bridge import EventBridge
from runtime.feedback.event_emitter import FeedbackEventEmitter
from runtime.feedback.models import Decision, FeedbackRecord


def _make_record(
    *,
    decision: Decision = Decision.APPROVE,
    reason: str = "very_relevant",
) -> FeedbackRecord:
    return FeedbackRecord(
        id=str(uuid.uuid4()),
        article_id="art-001",
        provider="google_news_ai",
        source="https://example.com",
        category="ai",
        topic="llm",
        recommended_score=0.85,
        recommendation="Test rec",
        decision=decision,
        reason=reason,
        comment=None,
        user_id="test-user",
        timestamp=datetime.now(timezone.utc),
        algorithm_version="1.0.0",
        feature_snapshot_version="1.0.0",
        dataset_version="1.0.0",
    )


class TestFeedbackEventEmitter:
    """Tests for FeedbackEventEmitter."""

    def test_emit_feedback_recorded(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        record = _make_record()

        emitter.emit_feedback_recorded(record)

        events = bridge.drain()
        assert len(events) == 1
        assert events[0].event_type == "feedback.recorded"
        assert events[0].payload["record_id"] == record.id
        assert events[0].payload["article_id"] == "art-001"

    def test_emit_session_started(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)

        emitter.emit_decision_session_started("session-001", "user-001")

        events = bridge.drain()
        assert len(events) == 1
        assert events[0].event_type == "feedback.session.started"
        assert events[0].payload["session_id"] == "session-001"

    def test_emit_session_ended(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        stats = {"approved": 3, "rejected": 1}

        emitter.emit_decision_session_ended("session-001", stats)

        events = bridge.drain()
        assert len(events) == 1
        assert events[0].event_type == "feedback.session.ended"
        assert events[0].payload["stats"] == stats

    def test_emit_learning_signal_approved(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        record = _make_record(decision=Decision.APPROVE)

        emitter.emit_learning_signal(record)

        events = bridge.drain()
        assert len(events) == 1
        assert events[0].event_type == "learning.signal.approved"
        assert events[0].payload["article_id"] == "art-001"

    def test_emit_learning_signal_rejected(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        record = _make_record(decision=Decision.REJECT, reason="low_quality")

        emitter.emit_learning_signal(record)

        events = bridge.drain()
        assert len(events) == 1
        assert events[0].event_type == "learning.signal.rejected"
        assert events[0].payload["reason"] == "low_quality"

    def test_emit_learning_signal_skip_no_event(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        record = _make_record(decision=Decision.SKIP)

        emitter.emit_learning_signal(record)

        events = bridge.drain()
        assert len(events) == 0

    def test_multiple_events_buffered(self):
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)

        emitter.emit_feedback_recorded(_make_record())
        emitter.emit_decision_session_started("s1", "u1")
        emitter.emit_learning_signal(_make_record())

        events = bridge.drain()
        assert len(events) == 3
        event_types = [e.event_type for e in events]
        assert "feedback.recorded" in event_types
        assert "feedback.session.started" in event_types
        assert "learning.signal.approved" in event_types
