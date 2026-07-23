"""
Tests for feedback data models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from runtime.feedback.models import Decision, DecisionSession, FeedbackRecord


class TestDecision:
    """Tests for Decision enum."""

    def test_decision_approve_value(self):
        assert Decision.APPROVE.value == "approve"

    def test_decision_reject_value(self):
        assert Decision.REJECT.value == "reject"

    def test_decision_skip_value(self):
        assert Decision.SKIP.value == "skip"

    def test_decision_from_value(self):
        assert Decision("approve") == Decision.APPROVE
        assert Decision("reject") == Decision.REJECT
        assert Decision("skip") == Decision.SKIP

    def test_decision_invalid_value(self):
        with pytest.raises(ValueError):
            Decision("invalid")


class TestFeedbackRecord:
    """Tests for FeedbackRecord dataclass."""

    def _make_record(self, **overrides) -> FeedbackRecord:
        defaults = {
            "id": str(uuid.uuid4()),
            "article_id": "art-001",
            "provider": "google_news_ai",
            "source": "https://example.com/article",
            "category": "ai",
            "topic": "llm",
            "recommended_score": 0.85,
            "recommendation": "High relevance to AI channel",
            "decision": Decision.APPROVE,
            "reason": "very_relevant",
            "comment": None,
            "user_id": "user-001",
            "timestamp": datetime.now(timezone.utc),
            "algorithm_version": "1.0.0",
            "feature_snapshot_version": "1.0.0",
            "dataset_version": "1.0.0",
        }
        defaults.update(overrides)
        return FeedbackRecord(**defaults)

    def test_creation_with_defaults(self):
        record = self._make_record()
        assert record.article_id == "art-001"
        assert record.decision == Decision.APPROVE
        assert record.comment is None

    def test_immutability(self):
        record = self._make_record()
        with pytest.raises(AttributeError):
            record.article_id = "art-002"

    def test_creation_with_comment(self):
        record = self._make_record(
            decision=Decision.REJECT,
            reason="low_quality",
            comment="Article has no substance",
        )
        assert record.comment == "Article has no substance"
        assert record.decision == Decision.REJECT

    def test_all_decision_types(self):
        for decision in Decision:
            record = self._make_record(decision=decision)
            assert record.decision == decision

    def test_timestamp_is_datetime(self):
        record = self._make_record()
        assert isinstance(record.timestamp, datetime)

    def test_scores_are_float(self):
        record = self._make_record(recommended_score=0.42)
        assert record.recommended_score == 0.42
        assert isinstance(record.recommended_score, float)


class TestDecisionSession:
    """Tests for DecisionSession dataclass."""

    def test_creation(self):
        session = DecisionSession(
            id=str(uuid.uuid4()),
            user_id="user-001",
            started_at=datetime.now(timezone.utc),
        )
        assert session.ended_at is None
        assert session.decisions == []
        assert session.stats == {}

    def test_with_decisions(self):
        record = FeedbackRecord(
            id=str(uuid.uuid4()),
            article_id="art-001",
            provider="google_news_ai",
            source="https://example.com",
            category="ai",
            topic="llm",
            recommended_score=0.85,
            recommendation="Test",
            decision=Decision.APPROVE,
            reason="very_relevant",
            comment=None,
            user_id="user-001",
            timestamp=datetime.now(timezone.utc),
            algorithm_version="1.0.0",
            feature_snapshot_version="1.0.0",
            dataset_version="1.0.0",
        )
        session = DecisionSession(
            id=str(uuid.uuid4()),
            user_id="user-001",
            started_at=datetime.now(timezone.utc),
            decisions=[record],
        )
        assert len(session.decisions) == 1
        assert session.decisions[0].id == record.id

    def test_mutable_session(self):
        session = DecisionSession(
            id=str(uuid.uuid4()),
            user_id="user-001",
            started_at=datetime.now(timezone.utc),
        )
        session.ended_at = datetime.now(timezone.utc)
        assert session.ended_at is not None

    def test_stats_default_empty(self):
        session = DecisionSession(
            id=str(uuid.uuid4()),
            user_id="user-001",
            started_at=datetime.now(timezone.utc),
        )
        assert session.stats == {}
