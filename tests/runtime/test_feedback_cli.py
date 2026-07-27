"""
Tests for feedback CLI — Sprint 8.3.1 Experience Polish.

Covers:
- Score color thresholds
- Card display (all fields, missing fields, fallback)
- "Why this recommendation?" section
- Shortcuts (A, R, S, Q, O, U)
- Numbered reason menu
- Undo functionality
- Progress bar
- Session stats tracking
- Decision diff (system vs human)
- Session summary
- Ctrl+C handling
- Open URL
- Existing tests preserved (decision flow, stats, analytics)
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch, call

import pytest

from runtime.feedback.cli import FeedbackCLI, SessionStats, _score_color
from runtime.feedback.models import Decision
from runtime.feedback.queue import DecisionQueue, QueueItem
from runtime.feedback.reasons import FeedbackReasons


# ── Score Color ──────────────────────────────────────────────────────


class TestScoreColor:
    """Score color mapping."""

    def test_high_score_green(self) -> None:
        assert _score_color(0.95) == "green"
        assert _score_color(0.80) == "green"

    def test_medium_score_yellow(self) -> None:
        assert _score_color(0.79) == "yellow"
        assert _score_color(0.50) == "yellow"

    def test_low_score_red(self) -> None:
        assert _score_color(0.49) == "red"
        assert _score_color(0.0) == "red"

    def test_boundary_exact_80(self) -> None:
        assert _score_color(0.80) == "green"

    def test_boundary_exact_50(self) -> None:
        assert _score_color(0.50) == "yellow"


# ── Session Stats ────────────────────────────────────────────────────


class TestSessionStats:
    """SessionStats tracking."""

    def test_initial_state(self) -> None:
        stats = SessionStats()
        assert stats.total == 0
        assert stats.approved == 0
        assert stats.rejected == 0
        assert stats.skipped == 0
        assert stats.processed == 0
        assert stats.records_sent == 0

    def test_processed_count(self) -> None:
        stats = SessionStats(approved=3, rejected=1, skipped=2)
        assert stats.processed == 6

    def test_avg_time_empty(self) -> None:
        stats = SessionStats()
        assert stats.avg_time == 0.0

    def test_avg_time_with_decisions(self) -> None:
        stats = SessionStats(decision_times=[10.0, 20.0, 30.0])
        assert stats.avg_time == 20.0

    def test_eta_for(self) -> None:
        stats = SessionStats(decision_times=[10.0, 20.0])
        # avg = 15.0, remaining = 4 → ETA = 60.0
        assert stats.eta_for(4) == 60.0

    def test_eta_for_no_data(self) -> None:
        stats = SessionStats()
        assert stats.eta_for(10) == 0.0


# ── CLI Queue ────────────────────────────────────────────────────────


class TestFeedbackCLIQueue:
    """CLI with queue interaction."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_show_next_item_empty_queue(self) -> None:
        with patch.object(self.cli._console, "print"):
            result = self.cli.show_next_item()
            assert result is None

    def test_show_next_item_returns_item_and_id(self) -> None:
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

    def test_set_total(self) -> None:
        self.cli.set_total(10)
        assert self.cli.session_stats.total == 10
        assert self.cli._items_total == 10


# ── Card Display ─────────────────────────────────────────────────────


class TestFeedbackCLICardDisplay:
    """Card rendering — all fields, missing fields, fallback."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _add_item(self, **kwargs) -> QueueItem:
        defaults = dict(
            article_id="art-001",
            provider="rss",
            source="https://example.com",
            category="tech",
            topic="ai",
            score=0.85,
            recommendation="APPROVE",
        )
        defaults.update(kwargs)
        result = self.queue.add(**defaults)
        return result.value

    def _get_panel_content(self, item: QueueItem) -> str:
        panel = self.cli._build_card(item)
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120)
        buf.print(panel)
        return buf.file.getvalue()

    def test_full_item_displays_all_fields(self) -> None:
        item = self._add_item(
            title="GPT-5 Released",
            url="https://example.com/gpt5",
            published="2026-07-27",
            summary="OpenAI releases GPT-5.",
        )
        content = self._get_panel_content(item)
        assert "GPT-5 Released" in content
        assert "https://example.com/gpt5" in content
        assert "2026-07-27" in content
        assert "OpenAI releases GPT-5." in content

    def test_missing_optional_fields_still_renders(self) -> None:
        item = self._add_item(title=None, url=None, published=None, summary=None)
        content = self._get_panel_content(item)
        assert "Provider" in content
        assert "Score" in content

    def test_summary_fallback_to_metadata(self) -> None:
        item = self._add_item(summary=None, metadata={"summary": "Meta text"})
        content = self._get_panel_content(item)
        assert "Meta text" in content

    def test_url_fallback_to_metadata(self) -> None:
        item = self._add_item(url=None, metadata={"url": "https://meta.url"})
        content = self._get_panel_content(item)
        assert "https://meta.url" in content

    def test_score_appears_in_card(self) -> None:
        item = self._add_item(score=0.92)
        content = self._get_panel_content(item)
        assert "0.92" in content


# ── Why Section ──────────────────────────────────────────────────────


class TestFeedbackCLIWhySection:
    """'Why this recommendation?' section rendering."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _make_item(self, reasons_data: dict | None) -> QueueItem:
        metadata = {}
        if reasons_data is not None:
            metadata["reasons"] = reasons_data
        result = self.queue.add(
            article_id="art-002", provider="rss", source="https://example.com",
            category="tech", topic="ai", score=0.85, recommendation="APPROVE",
            metadata=metadata,
        )
        return result.value

    def _render(self, item: QueueItem) -> str:
        from io import StringIO
        from rich.console import Console
        panel = self.cli._build_card(item)
        buf = Console(file=StringIO(), width=120)
        buf.print(panel)
        return buf.file.getvalue()

    def test_why_section_with_all_reasons(self) -> None:
        item = self._make_item({
            "source_quality": 0.93, "freshness": "High",
            "keywords": ["GPT-5", "LLM"], "similar_approved": 42, "confidence": 0.91,
        })
        content = self._render(item)
        assert "Why this recommendation?" in content
        assert "0.93" in content
        assert "High" in content
        assert "GPT-5" in content

    def test_why_section_no_reasons(self) -> None:
        item = self._make_item(None)
        content = self._render(item)
        assert "Why this recommendation?" not in content


# ── Shortcuts ────────────────────────────────────────────────────────


class TestFeedbackCLIShortcuts:
    """Keyboard shortcut handling."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_approve_shortcut_a(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="A"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.APPROVE

    def test_approve_shortcut_approve(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="approve"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.APPROVE

    def test_reject_shortcut_r(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="R"), \
             patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["R", "1"]
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.REJECT

    def test_skip_shortcut_s(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="S"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP

    def test_quit_shortcut_q(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="Q"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP
            assert reason == "quit"

    def test_quit_shortcut_quit(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="quit"):
            decision, reason, comment = self.cli.get_decision()
            assert reason == "quit"

    def test_legacy_number_1(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="1"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.APPROVE

    def test_legacy_number_3(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask", return_value="3"):
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP

    def test_unknown_command_retries(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["X", "S"]
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP
            assert mock_prompt.call_count == 2


# ── Numbered Reason Menu ────────────────────────────────────────────


class TestFeedbackCLIReasonMenu:
    """Numbered reason selection."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_reject_with_numbered_reason(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["R", "2"]
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.REJECT
            # "2" should map to the second reason in the catalog
            all_reasons = self.reasons.list_all()
            assert reason == all_reasons[1].code

    def test_reject_other_requires_comment(self) -> None:
        with patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            all_reasons = self.reasons.list_all()
            other_idx = next(
                i for i, r in enumerate(all_reasons, 1) if r.code == "other"
            )
            mock_prompt.side_effect = ["R", str(other_idx), "Custom text"]
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.REJECT
            assert reason == "other"
            assert comment == "Custom text"


# ── Undo ─────────────────────────────────────────────────────────────


class TestFeedbackCLIUndo:
    """Undo last decision."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _add_item(self, **kwargs) -> QueueItem:
        defaults = dict(
            article_id="art-001", provider="rss", source="https://example.com",
            category="tech", topic="ai", score=0.85, recommendation="APPROVE",
        )
        defaults.update(kwargs)
        return self.queue.add(**defaults).value

    def test_undo_restores_item_to_queue(self) -> None:
        item = self._add_item()
        self.cli.record_decision(item, Decision.APPROVE, "other", None)
        assert len(self.cli._undo_stack) == 1

        with patch.object(self.cli._console, "print"):
            self.cli._undo_last()

        assert len(self.cli._undo_stack) == 0
        # Item should be back in queue
        next_item = self.queue.get_next()
        assert next_item.is_success
        assert next_item.value is not None

    def test_undo_decrements_stats(self) -> None:
        item = self._add_item()
        self.cli.record_decision(item, Decision.APPROVE, "other", None)
        assert self.cli.session_stats.approved == 1

        with patch.object(self.cli._console, "print"):
            self.cli._undo_last()

        assert self.cli.session_stats.approved == 0

    def test_undo_empty_stack(self) -> None:
        with patch.object(self.cli._console, "print"):
            self.cli._undo_last()
        # Should not crash

    def test_undo_reject_decrements(self) -> None:
        item = self._add_item()
        self.cli.record_decision(item, Decision.REJECT, "low_relevance", None)
        assert self.cli.session_stats.rejected == 1

        with patch.object(self.cli._console, "print"):
            self.cli._undo_last()

        assert self.cli.session_stats.rejected == 0


# ── Progress Bar ─────────────────────────────────────────────────────


class TestFeedbackCLIProgress:
    """Progress bar display."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_show_progress_no_total(self) -> None:
        with patch.object(self.cli._console, "print"):
            # Should not crash with total=0
            self.cli.show_progress()

    def test_show_progress_with_total(self) -> None:
        from io import StringIO
        from rich.console import Console

        self.cli.set_total(10)
        buf = Console(file=StringIO(), width=120, no_color=True)
        # Swap the CLI's console so print goes to our buffer
        original_console = self.cli._console
        self.cli._console = buf
        try:
            self.cli.show_progress()
        finally:
            self.cli._console = original_console
        content = buf.file.getvalue()
        # After processing 1 item (from set_total -> processed starts at 1), show "1/10"
        assert "1/10" in content


# ── Decision Diff ────────────────────────────────────────────────────


class TestFeedbackCLIDiff:
    """System recommendation vs human decision display."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _make_item(self, recommendation: str) -> QueueItem:
        return self.queue.add(
            article_id="art-001", provider="rss", source="https://example.com",
            category="tech", topic="ai", score=0.85, recommendation=recommendation,
        ).value

    def test_same_decision_no_diff(self) -> None:
        item = self._make_item("APPROVE")
        with patch.object(self.cli._console, "print") as mock_print:
            self.cli.show_decision_diff(item, Decision.APPROVE)
            mock_print.assert_not_called()

    def test_different_decision_shows_diff(self) -> None:
        item = self._make_item("APPROVE")
        with patch.object(self.cli._console, "print") as mock_print:
            self.cli.show_decision_diff(item, Decision.REJECT)
            mock_print.assert_called_once()
            content = str(mock_print.call_args)
            assert "System:" in content
            assert "You:" in content

    def test_reject_to_approve_diff(self) -> None:
        item = self._make_item("REJECT")
        with patch.object(self.cli._console, "print") as mock_print:
            self.cli.show_decision_diff(item, Decision.APPROVE)
            content = str(mock_print.call_args)
            assert "APPROVE" in content


# ── Open URL ─────────────────────────────────────────────────────────


class TestFeedbackCLIOpenURL:
    """Open URL in browser."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_open_url_with_last_item(self) -> None:
        self.cli._last_item = QueueItem(
            id="test", article_id="a", provider="rss", source="s",
            category="c", topic="t", score=0.8, recommendation="APPROVE",
            url="https://example.com",
        )
        with patch("runtime.feedback.cli.webbrowser.open") as mock_open, \
             patch.object(self.cli._console, "print"):
            self.cli._open_url()
            mock_open.assert_called_once_with("https://example.com")

    def test_open_url_no_item(self) -> None:
        with patch.object(self.cli._console, "print"):
            self.cli._open_url()
            # Should not crash

    def test_open_url_no_url(self) -> None:
        self.cli._last_item = QueueItem(
            id="test", article_id="a", provider="rss", source="s",
            category="c", topic="t", score=0.8, recommendation="APPROVE",
        )
        with patch.object(self.cli._console, "print"):
            self.cli._open_url()
            # Should not crash

    def test_open_url_fallback_to_metadata(self) -> None:
        self.cli._last_item = QueueItem(
            id="test", article_id="a", provider="rss", source="s",
            category="c", topic="t", score=0.8, recommendation="APPROVE",
            metadata={"url": "https://from-meta.com"},
        )
        with patch("runtime.feedback.cli.webbrowser.open") as mock_open, \
             patch.object(self.cli._console, "print"):
            self.cli._open_url()
            mock_open.assert_called_once_with("https://from-meta.com")


# ── Session Summary ──────────────────────────────────────────────────


class TestFeedbackCLISessionSummary:
    """Extended session summary display."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_session_summary_renders(self) -> None:
        self.cli.set_total(8)
        self.cli._session_stats.approved = 5
        self.cli._session_stats.rejected = 2
        self.cli._session_stats.skipped = 1
        self.cli._session_stats.decision_times = [time.time() - i for i in range(8)]

        analytics = {
            "total_records": 7,
            "approval_rate": 0.71,
            "rejection_rate": 0.29,
            "top_reasons": [{"reason": "low_relevance", "count": 2}],
            "top_sources": [],
            "category_stats": [
                {"category": "ai", "approval_rate": 0.8, "total": 5, "approved": 4},
                {"category": "gaming", "approval_rate": 0.5, "total": 2, "approved": 1},
            ],
        }

        with patch.object(self.cli._console, "print"):
            # Should not raise
            self.cli.show_session_summary(analytics, records_sent=7)

    def test_session_summary_empty(self) -> None:
        analytics = {
            "total_records": 0, "approval_rate": 0.0, "rejection_rate": 0.0,
            "top_reasons": [], "top_sources": [], "category_stats": [],
        }
        with patch.object(self.cli._console, "print"):
            self.cli.show_session_summary(analytics, records_sent=0)


# ── Record Decision ──────────────────────────────────────────────────


class TestFeedbackCLIRecordDecision:
    """Recording decisions for stats and undo."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _make_item(self) -> QueueItem:
        return self.queue.add(
            article_id="art-001", provider="rss", source="https://example.com",
            category="tech", topic="ai", score=0.85, recommendation="APPROVE",
        ).value

    def test_record_approve(self) -> None:
        item = self._make_item()
        self.cli.record_decision(item, Decision.APPROVE, "other", None)
        assert self.cli.session_stats.approved == 1
        assert len(self.cli._undo_stack) == 1

    def test_record_reject(self) -> None:
        item = self._make_item()
        self.cli.record_decision(item, Decision.REJECT, "low_relevance", None)
        assert self.cli.session_stats.rejected == 1

    def test_record_skip(self) -> None:
        item = self._make_item()
        self.cli.record_decision(item, Decision.SKIP, "other", None)
        assert self.cli.session_stats.skipped == 1


# ── Legacy Stats & Analytics ─────────────────────────────────────────


class TestFeedbackCLIStats:
    """Stats and analytics display — backward compat."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_show_stats(self) -> None:
        stats = {"pending": 5, "approved": 3, "rejected": 1, "skipped": 1, "total": 10}
        with patch.object(self.cli._console, "print"):
            self.cli.show_stats(stats)

    def test_show_analytics(self) -> None:
        analytics = {
            "total_records": 10, "approval_rate": 0.6, "rejection_rate": 0.4,
            "top_reasons": [{"reason": "low_relevance", "count": 3}],
            "top_sources": [{"source": "example.com", "approval_rate": 0.8}],
        }
        with patch.object(self.cli._console, "print"):
            self.cli.show_analytics(analytics)
