"""
Tests for feedback CLI (mocked — no actual Rich output).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from runtime.feedback.cli import FeedbackCLI
from runtime.feedback.queue import DecisionQueue
from runtime.feedback.reasons import FeedbackReasons


class TestFeedbackCLI:
    """Tests for FeedbackCLI (unit tests with mocked I/O)."""

    def setup_method(self):
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_show_next_item_empty_queue(self):
        with patch.object(self.cli._console, "print"):
            result = self.cli.show_next_item()
            assert result is None

    def test_show_next_item_with_data(self):
        self.queue.add(
            article_id="art-001",
            provider="google_news_ai",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test",
        )
        with patch.object(self.cli._console, "print"):
            result = self.cli.show_next_item()
            assert result is not None
            assert "item" in result
            assert "id" in result

    def test_get_decision_approve(self):
        with patch("runtime.feedback.cli.IntPrompt.ask", return_value=1):
            decision, reason, comment = self.cli.get_decision()
            assert decision.value == "approve"

    def test_get_decision_reject(self):
        with patch("runtime.feedback.cli.IntPrompt.ask", return_value=2), \
             patch("runtime.feedback.cli.Prompt.ask", return_value="low_relevance"):
            decision, reason, comment = self.cli.get_decision()
            assert decision.value == "reject"
            assert reason == "low_relevance"

    def test_get_decision_skip(self):
        with patch("runtime.feedback.cli.IntPrompt.ask", return_value=3):
            decision, reason, comment = self.cli.get_decision()
            assert decision.value == "skip"

    def test_get_decision_reject_other(self):
        with patch("runtime.feedback.cli.IntPrompt.ask", return_value=2), \
             patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["other", "Custom reason text"]
            decision, reason, comment = self.cli.get_decision()
            assert decision.value == "reject"
            assert reason == "other"
            assert comment == "Custom reason text"

    def test_show_stats(self):
        stats = {"pending": 5, "approved": 3, "rejected": 1, "skipped": 1, "total": 10}
        with patch.object(self.cli._console, "print"):
            # Should not raise
            self.cli.show_stats(stats)

    def test_show_analytics(self):
        analytics = {
            "total_records": 10,
            "approval_rate": 0.6,
            "rejection_rate": 0.4,
            "top_reasons": [{"reason": "low_relevance", "count": 3}],
            "top_sources": [{"source": "example.com", "approval_rate": 0.8}],
        }
        with patch.object(self.cli._console, "print"):
            # Should not raise
            self.cli.show_analytics(analytics)
