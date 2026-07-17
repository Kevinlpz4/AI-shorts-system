"""Tests for FeedbackRecord Aggregate Root — IMMUTABLE."""
import pytest
from datetime import datetime, timezone
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import FeedbackId
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot


def _make_snapshot():
    return FeatureSnapshot(
        base_score=0.7, freshness_score=0.8, keyword_bonus=0.1,
        source_bonus=0.2, topic_penalty=0.05, confidence=0.9,
        final_score=0.75, timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
    )


def _make_feedback(**overrides):
    defaults = dict(
        id=FeedbackId.generate(),
        topic_id="topic-001",
        decision=DecisionType.APPROVED,
        reason=None,
        feature_snapshot=_make_snapshot(),
        source_name="reddit",
        title="Test Article",
    )
    defaults.update(overrides)
    return FeedbackRecord(**defaults)


class TestFeedbackRecord:
    def test_valid_approved(self):
        fr = _make_feedback()
        assert fr.topic_id == "topic-001"
        assert fr.decision == DecisionType.APPROVED
        assert fr.source_name == "reddit"

    def test_valid_rejected_with_reason(self):
        fr = _make_feedback(
            decision=DecisionType.REJECTED,
            reason="LOW_QUALITY",
        )
        assert fr.decision == DecisionType.REJECTED
        assert fr.reason == "LOW_QUALITY"

    def test_valid_auto_approved(self):
        fr = _make_feedback(decision=DecisionType.AUTO_APPROVED)
        assert fr.decision == DecisionType.AUTO_APPROVED

    def test_valid_overridden_with_reason(self):
        fr = _make_feedback(decision=DecisionType.OVERRIDDEN, reason="CLICKBAIT")
        assert fr.decision == DecisionType.OVERRIDDEN

    def test_rejects_empty_topic_id(self):
        with pytest.raises(Exception):
            _make_feedback(topic_id="")

    def test_rejects_empty_source_name(self):
        with pytest.raises(Exception):
            _make_feedback(source_name="")

    def test_rejects_rejected_without_reason(self):
        with pytest.raises(Exception, match="reason is required"):
            _make_feedback(decision=DecisionType.REJECTED, reason=None)

    def test_rejects_auto_rejected_without_reason(self):
        with pytest.raises(Exception, match="reason is required"):
            _make_feedback(decision=DecisionType.AUTO_REJECTED, reason=None)

    def test_rejects_overridden_without_reason(self):
        with pytest.raises(Exception, match="reason is required"):
            _make_feedback(decision=DecisionType.OVERRIDDEN, reason=None)

    def test_approved_without_reason_is_ok(self):
        fr = _make_feedback(decision=DecisionType.APPROVED, reason=None)
        assert fr.reason is None

    def test_immutable_cannot_set_attribute(self):
        fr = _make_feedback()
        with pytest.raises(AttributeError, match="immutable"):
            fr.topic_id = "hacked"  # type: ignore[misc]

    def test_immutable_cannot_set_decision(self):
        fr = _make_feedback()
        with pytest.raises(AttributeError, match="immutable"):
            fr.decision = DecisionType.REJECTED  # type: ignore[misc]

    def test_emits_feedback_captured_event(self):
        fr = _make_feedback()
        events = fr.pull_events()
        assert len(events) == 1
        assert events[0].__class__.__name__ == "FeedbackCaptured"

    def test_event_contains_correct_data(self):
        fr = _make_feedback(topic_id="t-42", source_name="hn")
        events = fr.pull_events()
        ev = events[0]
        assert ev.topic_id == "t-42"
        assert ev.source_name == "hn"
        assert ev.decision == DecisionType.APPROVED

    def test_captured_at_defaults_to_now(self):
        fr = _make_feedback()
        assert fr.captured_at is not None
        assert fr.captured_at.tzinfo is not None

    def test_score_snapshot_defaults_to_empty_dict(self):
        fr = _make_feedback()
        assert fr.score_snapshot == {}

    def test_topic_id_stripped(self):
        fr = _make_feedback(topic_id="  topic-001  ")
        assert fr.topic_id == "topic-001"

    def test_source_name_stripped(self):
        fr = _make_feedback(source_name="  reddit  ")
        assert fr.source_name == "reddit"
