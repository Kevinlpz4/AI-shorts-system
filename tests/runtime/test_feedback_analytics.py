"""
Tests for analytics collector.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from runtime.feedback.analytics import AnalyticsCollector
from runtime.feedback.models import Decision, FeedbackRecord


def _make_record(
    *,
    decision: Decision = Decision.APPROVE,
    reason: str = "very_relevant",
    source: str = "https://example.com",
    category: str = "ai",
    topic: str = "llm",
    score: float = 0.85,
    days_ago: int = 0,
) -> FeedbackRecord:
    """Factory helper for test records."""
    return FeedbackRecord(
        id=str(uuid.uuid4()),
        article_id=f"art-{uuid.uuid4().hex[:6]}",
        provider="google_news_ai",
        source=source,
        category=category,
        topic=topic,
        recommended_score=score,
        recommendation="Test recommendation",
        decision=decision,
        reason=reason,
        comment=None,
        user_id="test-user",
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
        algorithm_version="1.0.0",
        feature_snapshot_version="1.0.0",
        dataset_version="1.0.0",
    )


class TestAnalyticsCollector:
    """Tests for AnalyticsCollector."""

    def test_empty_collector(self):
        analytics = AnalyticsCollector()
        assert analytics.get_approval_rate() == 0.0
        assert analytics.get_rejection_rate() == 0.0

    def test_approval_rate(self):
        analytics = AnalyticsCollector()
        analytics.add_record(_make_record(decision=Decision.APPROVE))
        analytics.add_record(_make_record(decision=Decision.APPROVE))
        analytics.add_record(_make_record(decision=Decision.REJECT))
        assert analytics.get_approval_rate() == pytest.approx(2 / 3)

    def test_rejection_rate(self):
        analytics = AnalyticsCollector()
        analytics.add_record(_make_record(decision=Decision.APPROVE))
        analytics.add_record(_make_record(decision=Decision.REJECT))
        analytics.add_record(_make_record(decision=Decision.REJECT))
        assert analytics.get_rejection_rate() == pytest.approx(2 / 3)

    def test_top_reasons(self):
        analytics = AnalyticsCollector()
        for _ in range(5):
            analytics.add_record(_make_record(
                decision=Decision.REJECT, reason="low_relevance"
            ))
        for _ in range(3):
            analytics.add_record(_make_record(
                decision=Decision.REJECT, reason="clickbait"
            ))
        for _ in range(1):
            analytics.add_record(_make_record(
                decision=Decision.REJECT, reason="duplicate"
            ))

        top = analytics.get_top_reasons(limit=2)
        assert len(top) == 2
        assert top[0]["reason"] == "low_relevance"
        assert top[0]["count"] == 5
        assert top[1]["reason"] == "clickbait"
        assert top[1]["count"] == 3

    def test_top_reasons_empty(self):
        analytics = AnalyticsCollector()
        assert analytics.get_top_reasons() == []

    def test_top_sources(self):
        analytics = AnalyticsCollector()
        # Source A: 3/4 approved (75%)
        for _ in range(3):
            analytics.add_record(_make_record(
                source="source-a", decision=Decision.APPROVE
            ))
        analytics.add_record(_make_record(
            source="source-a", decision=Decision.REJECT
        ))
        # Source B: 2/4 approved (50%)
        for _ in range(2):
            analytics.add_record(_make_record(
                source="source-b", decision=Decision.APPROVE
            ))
        for _ in range(2):
            analytics.add_record(_make_record(
                source="source-b", decision=Decision.REJECT
            ))
        # Source C: 1/2 (< 3 min threshold — excluded)
        analytics.add_record(_make_record(
            source="source-c", decision=Decision.APPROVE
        ))
        analytics.add_record(_make_record(
            source="source-c", decision=Decision.REJECT
        ))

        top = analytics.get_top_sources(limit=5)
        # source-c excluded (< 3 items)
        assert len(top) == 2
        assert top[0]["source"] == "source-a"
        assert top[0]["approval_rate"] == pytest.approx(0.75)

    def test_worst_sources(self):
        analytics = AnalyticsCollector()
        # Source A: 1/3 approved (33%)
        analytics.add_record(_make_record(
            source="source-a", decision=Decision.APPROVE
        ))
        for _ in range(2):
            analytics.add_record(_make_record(
                source="source-a", decision=Decision.REJECT
            ))
        # Source B: 3/3 approved (100%)
        for _ in range(3):
            analytics.add_record(_make_record(
                source="source-b", decision=Decision.APPROVE
            ))

        worst = analytics.get_worst_sources(limit=1)
        assert len(worst) == 1
        assert worst[0]["source"] == "source-a"

    def test_category_stats(self):
        analytics = AnalyticsCollector()
        for _ in range(3):
            analytics.add_record(_make_record(
                category="ai", decision=Decision.APPROVE
            ))
        for _ in range(1):
            analytics.add_record(_make_record(
                category="ai", decision=Decision.REJECT
            ))
        for _ in range(1):
            analytics.add_record(_make_record(
                category="gaming", decision=Decision.APPROVE
            ))

        stats = analytics.get_category_stats()
        assert len(stats) == 2
        ai_stats = next(s for s in stats if s["category"] == "ai")
        assert ai_stats["approval_rate"] == pytest.approx(0.75)
        assert ai_stats["total"] == 4

    def test_keyword_stats(self):
        analytics = AnalyticsCollector()
        for _ in range(4):
            analytics.add_record(_make_record(
                topic="llm", decision=Decision.APPROVE
            ))
        analytics.add_record(_make_record(
            topic="llm", decision=Decision.REJECT
        ))

        stats = analytics.get_keyword_stats()
        llm_stats = next(s for s in stats if s["topic"] == "llm")
        assert llm_stats["approval_rate"] == pytest.approx(0.8)

    def test_daily_evolution(self):
        analytics = AnalyticsCollector()
        # Today: 2 approved, 1 rejected
        analytics.add_record(_make_record(
            decision=Decision.APPROVE, days_ago=0
        ))
        analytics.add_record(_make_record(
            decision=Decision.APPROVE, days_ago=0
        ))
        analytics.add_record(_make_record(
            decision=Decision.REJECT, days_ago=0
        ))

        evolution = analytics.get_daily_evolution(days=1)
        assert len(evolution) == 1
        assert evolution[0]["total"] == 3
        assert evolution[0]["approved"] == 2
        assert evolution[0]["rejected"] == 1
        assert evolution[0]["approval_rate"] == pytest.approx(2 / 3)

    def test_weekly_evolution(self):
        analytics = AnalyticsCollector()
        # Add some records
        for _ in range(3):
            analytics.add_record(_make_record(decision=Decision.APPROVE))
        for _ in range(2):
            analytics.add_record(_make_record(decision=Decision.REJECT))

        evolution = analytics.get_weekly_evolution(weeks=1)
        assert len(evolution) >= 1
        total_approved = sum(e["approved"] for e in evolution)
        assert total_approved == 3

    def test_summary(self):
        analytics = AnalyticsCollector()
        for _ in range(3):
            analytics.add_record(_make_record(decision=Decision.APPROVE))
        for _ in range(2):
            analytics.add_record(_make_record(decision=Decision.REJECT))

        summary = analytics.get_summary()
        assert summary["total_records"] == 5
        assert summary["approval_rate"] == pytest.approx(0.6)
        assert summary["rejection_rate"] == pytest.approx(0.4)
        assert "top_reasons" in summary
        assert "top_sources" in summary
        assert "category_stats" in summary
        assert "keyword_stats" in summary
        assert "daily_evolution" in summary
        assert "weekly_evolution" in summary
