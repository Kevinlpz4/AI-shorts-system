"""
E2E integration tests for the complete feedback cycle.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from runtime.feedback.analytics import AnalyticsCollector
from runtime.feedback.event_emitter import FeedbackEventEmitter
from runtime.feedback.models import Decision, DecisionSession, FeedbackRecord
from runtime.feedback.queue import DecisionQueue
from runtime.feedback.reasons import FeedbackReasons
from runtime.event_bridge import EventBridge


def _make_queue_item_args(i: int) -> dict:
    return {
        "article_id": f"article-{i}",
        "provider": "google_news_ai",
        "source": f"https://example.com/article-{i}",
        "category": "ai",
        "topic": "llm",
        "score": 0.8 - (i * 0.05),
        "recommendation": f"Recommendation {i}",
    }


@pytest.mark.integration
class TestFeedbackE2E:
    """E2E tests for feedback cycle."""

    def test_complete_feedback_cycle(self):
        """Test complete feedback cycle from queue to analytics."""
        queue = DecisionQueue()
        analytics = AnalyticsCollector()

        # Add items to queue
        for i in range(5):
            queue.add(**_make_queue_item_args(i))

        # Process decisions
        for i in range(5):
            item_result = queue.get_next()
            assert item_result.is_success
            item = item_result.value

            decision = Decision.APPROVE if i < 3 else Decision.REJECT
            reason_code = "low_relevance" if decision == Decision.REJECT else None

            process_result = queue.process(
                item_id=item.id,
                decision=decision.value,
                reason=reason_code,
            )
            assert process_result.is_success

            # Add to analytics
            record = FeedbackRecord(
                id=str(uuid.uuid4()),
                article_id=item.article_id,
                provider=item.provider,
                source=item.source,
                category=item.category,
                topic=item.topic,
                recommended_score=item.score,
                recommendation=item.recommendation,
                decision=decision,
                reason=reason_code or "approved",
                comment=None,
                user_id="test-user",
                timestamp=datetime.now(timezone.utc),
                algorithm_version="1.0.0",
                feature_snapshot_version="1.0.0",
                dataset_version="1.0.0",
            )
            analytics.add_record(record)

        # Verify analytics
        assert analytics.get_approval_rate() == pytest.approx(0.6)  # 3/5
        assert analytics.get_rejection_rate() == pytest.approx(0.4)  # 2/5

        # Verify queue stats
        stats = queue.get_stats()
        assert stats["pending"] == 0
        assert stats["approved"] == 3
        assert stats["rejected"] == 2

    def test_feedback_with_event_emission(self):
        """Test feedback cycle with event emission to Learning BC."""
        queue = DecisionQueue()
        bridge = EventBridge()
        emitter = FeedbackEventEmitter(bridge)
        session_id = str(uuid.uuid4())

        emitter.emit_decision_session_started(session_id, "test-user")

        # Add and process items
        for i in range(3):
            result = queue.add(**_make_queue_item_args(i))
            item = result.value

            if i < 2:
                queue.process(item.id, decision="approved")
                record = FeedbackRecord(
                    id=str(uuid.uuid4()),
                    article_id=item.article_id,
                    provider=item.provider,
                    source=item.source,
                    category=item.category,
                    topic=item.topic,
                    recommended_score=item.score,
                    recommendation=item.recommendation,
                    decision=Decision.APPROVE,
                    reason="approved",
                    comment=None,
                    user_id="test-user",
                    timestamp=datetime.now(timezone.utc),
                    algorithm_version="1.0.0",
                    feature_snapshot_version="1.0.0",
                    dataset_version="1.0.0",
                )
                emitter.emit_learning_signal(record)
                emitter.emit_feedback_recorded(record)
            else:
                queue.process(item.id, decision="rejected")

        emitter.emit_decision_session_ended(session_id, queue.get_stats())

        events = bridge.drain()
        event_types = [e.event_type for e in events]

        assert "feedback.session.started" in event_types
        assert "learning.signal.approved" in event_types
        assert "feedback.recorded" in event_types
        assert "feedback.session.ended" in event_types

    def test_reasons_integration_with_queue(self):
        """Test that reason validation works with queue processing."""
        reasons = FeedbackReasons()
        queue = DecisionQueue()

        # Add item
        result = queue.add(**_make_queue_item_args(0))
        item = result.value

        # Validate reason before processing
        reason_code = "low_relevance"
        validation = reasons.validate(reason_code)
        assert validation.is_success

        # Process with valid reason
        process_result = queue.process(
            item_id=item.id,
            decision="rejected",
            reason=reason_code,
        )
        assert process_result.is_success

    def test_analytics_from_multiple_sources(self):
        """Test analytics correctly handles multiple sources and categories."""
        analytics = AnalyticsCollector()

        sources = ["source-a", "source-b", "source-c"]
        categories = ["ai", "gaming"]
        topics = ["llm", "gpu", "steam"]

        records = []
        for source in sources:
            for category in categories:
                for topic in topics:
                    for decision in [Decision.APPROVE, Decision.REJECT]:
                        record = FeedbackRecord(
                            id=str(uuid.uuid4()),
                            article_id=f"art-{uuid.uuid4().hex[:6]}",
                            provider="test",
                            source=source,
                            category=category,
                            topic=topic,
                            recommended_score=0.5,
                            recommendation="Test",
                            decision=decision,
                            reason="test",
                            comment=None,
                            user_id="test-user",
                            timestamp=datetime.now(timezone.utc),
                            algorithm_version="1.0.0",
                            feature_snapshot_version="1.0.0",
                            dataset_version="1.0.0",
                        )
                        records.append(record)
                        analytics.add_record(record)

        # Total: 3 sources * 2 categories * 3 topics * 2 decisions = 36
        summary = analytics.get_summary()
        assert summary["total_records"] == 36
        assert summary["approval_rate"] == pytest.approx(0.5)

        # Each source has 12 records, 6 approved = 50%
        top_sources = analytics.get_top_sources(limit=3)
        assert len(top_sources) == 3

    def test_session_workflow(self):
        """Test creating and completing a decision session."""
        queue = DecisionQueue()

        session = DecisionSession(
            id=str(uuid.uuid4()),
            user_id="test-user",
            started_at=datetime.now(timezone.utc),
        )

        # Add items
        for i in range(3):
            result = queue.add(**_make_queue_item_args(i))
            session.decisions.append(
                FeedbackRecord(
                    id=str(uuid.uuid4()),
                    article_id=result.value.article_id,
                    provider=result.value.provider,
                    source=result.value.source,
                    category=result.value.category,
                    topic=result.value.topic,
                    recommended_score=result.value.score,
                    recommendation=result.value.recommendation,
                    decision=Decision.APPROVE,
                    reason="very_relevant",
                    comment=None,
                    user_id="test-user",
                    timestamp=datetime.now(timezone.utc),
                    algorithm_version="1.0.0",
                    feature_snapshot_version="1.0.0",
                    dataset_version="1.0.0",
                )
            )

        session.stats = queue.get_stats()
        session.ended_at = datetime.now(timezone.utc)

        assert len(session.decisions) == 3
        assert session.ended_at is not None
        assert session.stats["total"] == 3
