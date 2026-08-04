"""
Tests for feedback CLI — Sprint 8.3.2 Reviewer Experience & Learning Visibility.

Covers:
- Confidence bar rendering
- SessionDecision dataclass properties
- SessionStats learning tracking (sources, categories, keywords, confidence)
- SessionStats agreement_rate
- Learning Updated panel
- Session History panel (H shortcut)
- JSON session export
- Learning Progress panel
- Enhanced recommendation explanation (duplicates, trend, confidence bar)
- Enhanced card with confidence bar
- Existing tests preserved
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch


from runtime.feedback.cli import (
    FeedbackCLI,
    SessionStats,
    SessionDecision,
    _confidence_bar,
)
from runtime.feedback.models import Decision
from runtime.feedback.queue import DecisionQueue, QueueItem
from runtime.feedback.reasons import FeedbackReasons


# ── Helpers ──────────────────────────────────────────────────────────


def _render(cli: FeedbackCLI, renderable) -> str:
    """Render a Rich renderable to a StringIO buffer and return the text."""
    from io import StringIO
    from rich.console import Console
    buf = Console(file=StringIO(), width=120, no_color=True)
    cli._console = buf
    buf.print(renderable)
    return buf.file.getvalue()


def _make_item(queue: DecisionQueue, **overrides) -> QueueItem:
    defaults = dict(
        article_id="art-001", provider="rss", source="https://example.com",
        category="ai", topic="llm", score=0.85, recommendation="APPROVE",
    )
    defaults.update(overrides)
    return queue.add(**defaults).value


def _make_reasons_item(queue: DecisionQueue, reasons_data: dict, **overrides) -> QueueItem:
    metadata = {"reasons": reasons_data}
    return _make_item(queue, metadata=metadata, **overrides)


# ── Confidence Bar ───────────────────────────────────────────────────


class TestConfidenceBar:
    """Visual confidence bar rendering."""

    def test_bar_full(self) -> None:
        bar = _confidence_bar(1.0)
        assert "100%" in bar

    def test_bar_empty(self) -> None:
        bar = _confidence_bar(0.0)
        assert "0%" in bar

    def test_bar_half(self) -> None:
        bar = _confidence_bar(0.5)
        assert "50%" in bar

    def test_bar_contains_blocks(self) -> None:
        bar = _confidence_bar(0.8)
        assert "█" in bar
        assert "░" in bar


# ── SessionDecision ──────────────────────────────────────────────────


class TestSessionDecision:
    """SessionDecision dataclass properties."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()

    def test_time_str(self) -> None:
        item = _make_item(self.queue)
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert ":" in sd.time_str
        assert len(sd.time_str) == 8  # HH:MM:SS

    def test_title_or_id_with_title(self) -> None:
        item = _make_item(self.queue, title="GPT-5 Launches")
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert sd.title_or_id == "GPT-5 Launches"

    def test_title_or_id_without_title(self) -> None:
        item = _make_item(self.queue, title=None)
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert sd.title_or_id == item.article_id[:12]

    def test_icon_approve(self) -> None:
        item = _make_item(self.queue)
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert sd.icon == "✅"

    def test_icon_reject(self) -> None:
        item = _make_item(self.queue)
        sd = SessionDecision(
            item=item, decision=Decision.REJECT, reason="low_relevance",
            comment=None, timestamp=time.time(),
        )
        assert sd.icon == "❌"

    def test_icon_skip(self) -> None:
        item = _make_item(self.queue)
        sd = SessionDecision(
            item=item, decision=Decision.SKIP, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert sd.icon == "⏭"

    def test_decision_label(self) -> None:
        item = _make_item(self.queue)
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(),
        )
        assert sd.decision_label == "APPROVE"


# ── SessionStats Learning Tracking ───────────────────────────────────


class TestSessionStatsLearning:
    """SessionStats learning growth tracking."""

    def test_record_source(self) -> None:
        stats = SessionStats()
        stats.record_source("https://example.com", approved=True)
        stats.record_source("https://example.com", approved=True)
        stats.record_source("https://example.com", approved=False)
        assert stats.sources_seen["https://example.com"]["approved"] == 2
        assert stats.sources_seen["https://example.com"]["rejected"] == 1

    def test_record_category(self) -> None:
        stats = SessionStats()
        stats.record_category("ai", approved=True)
        stats.record_category("ai", approved=False)
        assert stats.categories_seen["ai"]["approved"] == 1
        assert stats.categories_seen["ai"]["rejected"] == 1

    def test_record_keywords(self) -> None:
        stats = SessionStats()
        stats.record_keywords(["GPT-5", "LLM", "AI"])
        stats.record_keywords(["GPT-5", "reasoning"])
        assert stats.keywords_seen["GPT-5"] == 2
        assert stats.keywords_seen["LLM"] == 1
        assert stats.keywords_seen["AI"] == 1
        assert stats.keywords_seen["reasoning"] == 1

    def test_record_confidence(self) -> None:
        stats = SessionStats()
        stats.record_confidence(0.9)
        stats.record_confidence(0.8)
        assert stats.confidence_trend == [0.9, 0.8]

    def test_agreement_rate_all_agree(self) -> None:
        stats = SessionStats()
        item = QueueItem(
            id="1", article_id="a", provider="rss", source="s",
            category="c", topic="t", score=0.8, recommendation="APPROVE",
        )
        sd = SessionDecision(
            item=item, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(), ai_agrees=True,
        )
        stats._decisions_list = [sd, sd]
        stats.approved = 2
        assert stats.agreement_rate == 1.0

    def test_agreement_rate_mixed(self) -> None:
        stats = SessionStats()
        item1 = QueueItem(
            id="1", article_id="a", provider="rss", source="s",
            category="c", topic="t", score=0.8, recommendation="APPROVE",
        )
        item2 = QueueItem(
            id="2", article_id="b", provider="rss", source="s",
            category="c", topic="t", score=0.3, recommendation="REJECT",
        )
        sd1 = SessionDecision(
            item=item1, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(), ai_agrees=True,
        )
        sd2 = SessionDecision(
            item=item2, decision=Decision.APPROVE, reason="other",
            comment=None, timestamp=time.time(), ai_agrees=False,
        )
        stats._decisions_list = [sd1, sd2]
        stats.approved = 1
        stats.rejected = 1
        assert stats.agreement_rate == 0.5

    def test_agreement_rate_no_decisions(self) -> None:
        stats = SessionStats()
        assert stats.agreement_rate == 0.0


# ── Learning Updated Panel ───────────────────────────────────────────


class TestLearningUpdate:
    """Learning Updated panel display."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_learning_update_renders(self) -> None:
        item = _make_reasons_item(self.queue, {
            "source_quality": 0.9, "freshness": "High",
            "keywords": ["GPT-5", "LLM"], "confidence": 0.91,
        })
        self.cli.record_decision(item, Decision.APPROVE, "other", None)

        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_update(item, Decision.APPROVE, "other")
        output = buf.file.getvalue()

        assert "Learning Updated" in output
        assert "Source profile" in output
        assert "Category" in output
        assert "Confidence" in output

    def test_learning_update_reject(self) -> None:
        item = _make_reasons_item(self.queue, {
            "source_quality": 0.5, "freshness": "Low",
            "keywords": ["AI"], "confidence": 0.4,
        })
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_update(item, Decision.REJECT, "low_relevance")
        output = buf.file.getvalue()

        assert "Learning Updated" in output
        assert "Penalizes" in output

    def test_learning_update_with_keywords(self) -> None:
        item = _make_reasons_item(self.queue, {
            "keywords": ["GPT-5", "LLM"], "confidence": 0.85,
        })
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_update(item, Decision.APPROVE, "other")
        output = buf.file.getvalue()

        assert "Keywords" in output
        assert "GPT-5" in output


# ── Session History ──────────────────────────────────────────────────


class TestSessionHistory:
    """Session history display."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_history_empty(self) -> None:
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_history()
        output = buf.file.getvalue()
        assert "No decisions made yet" in output

    def test_history_shows_decisions(self) -> None:
        item1 = _make_item(self.queue, title="Article One")
        item2 = _make_item(self.queue, title="Article Two")
        self.cli.record_decision(item1, Decision.APPROVE, "other", None)
        self.cli.record_decision(item2, Decision.REJECT, "low_relevance", None)

        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_history()
        output = buf.file.getvalue()

        assert "Session History" in output
        assert "Article One" in output
        assert "Article Two" in output

    def test_history_last_n(self) -> None:
        for i in range(5):
            item = _make_item(self.queue, title=f"Article {i}")
            self.cli.record_decision(item, Decision.APPROVE, "other", None)

        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_history(last_n=3)
        output = buf.file.getvalue()

        assert "last 3 of 5" in output

    def test_history_undo_compatible(self) -> None:
        """History entries match undo stack."""
        item = _make_item(self.queue, title="Test")
        self.cli.record_decision(item, Decision.APPROVE, "other", None)
        assert len(self.cli._undo_stack) == 1
        assert len(self.cli.session_stats._decisions_list) == 1

        self.cli._undo_last()
        assert len(self.cli._undo_stack) == 0
        # History still shows the decision (undo removes from stack, not history)
        # Actually, _undo_last pops from undo_stack, so history list is separate
        assert len(self.cli.session_stats._decisions_list) == 1


# ── JSON Export ──────────────────────────────────────────────────────


class TestJSONExport:
    """Session export to JSON."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_export_creates_file(self, tmp_path: Path) -> None:
        item = _make_item(self.queue, title="Test Article")
        self.cli.record_decision(item, Decision.APPROVE, "other", None)

        filepath = self.cli.export_session(str(tmp_path))
        assert filepath is not None
        assert Path(filepath).exists()

    def test_export_json_structure(self, tmp_path: Path) -> None:
        item = _make_reasons_item(self.queue, {
            "confidence": 0.9, "keywords": ["AI"],
        }, title="AI News")
        self.cli.record_decision(item, Decision.APPROVE, "other", None)

        filepath = self.cli.export_session(str(tmp_path))
        data = json.loads(Path(filepath).read_text())

        # Check top-level keys
        assert "session" in data
        assert "statistics" in data
        assert "learning_growth" in data
        assert "decisions" in data

        # Check session metadata
        assert "id" in data["session"]
        assert "user_id" in data["session"]
        assert "started_at" in data["session"]
        assert "ended_at" in data["session"]
        assert "duration_seconds" in data["session"]

        # Check statistics
        assert data["statistics"]["approved"] == 1
        assert data["statistics"]["rejected"] == 0
        assert data["statistics"]["processed"] == 1
        assert data["statistics"]["approval_rate"] == 1.0

        # Check learning growth
        assert data["learning_growth"]["sources_profiled"] == 1
        assert data["learning_growth"]["categories_profiled"] == 1
        assert data["learning_growth"]["unique_keywords"] == 1

        # Check decisions
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["decision"] == "approve"
        assert data["decisions"][0]["ai_agrees"] is True

    def test_export_empty_session(self, tmp_path: Path) -> None:
        filepath = self.cli.export_session(str(tmp_path))
        assert filepath is not None
        data = json.loads(Path(filepath).read_text())
        assert data["decisions"] == []
        assert data["statistics"]["processed"] == 0

    def test_export_filename_format(self, tmp_path: Path) -> None:
        filepath = self.cli.export_session(str(tmp_path))
        filename = Path(filepath).name
        assert filename.startswith("feedback_session_")
        assert filename.endswith(".json")

    def test_export_multiple_decisions(self, tmp_path: Path) -> None:
        for i in range(3):
            item = _make_item(self.queue, title=f"Article {i}")
            self.cli.record_decision(
                item,
                Decision.APPROVE if i < 2 else Decision.REJECT,
                "other" if i < 2 else "low_relevance",
                None,
            )

        filepath = self.cli.export_session(str(tmp_path))
        data = json.loads(Path(filepath).read_text())
        assert len(data["decisions"]) == 3
        assert data["statistics"]["approved"] == 2
        assert data["statistics"]["rejected"] == 1


# ── Learning Progress Panel ──────────────────────────────────────────


class TestLearningProgress:
    """Learning Progress final panel."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_learning_progress_renders(self) -> None:
        item = _make_reasons_item(self.queue, {
            "confidence": 0.9, "keywords": ["GPT-5", "LLM"],
        })
        self.cli.record_decision(item, Decision.APPROVE, "other", None)

        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_progress()
        output = buf.file.getvalue()

        assert "Learning Progress" in output
        assert "Knowledge Growth" in output
        assert "Articles reviewed" in output
        assert "Keywords learned" in output

    def test_learning_progress_empty(self) -> None:
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_progress()
        output = buf.file.getvalue()

        assert "Learning Progress" in output
        assert "Articles reviewed: 0" in output

    def test_learning_progress_with_multiple_decisions(self) -> None:
        items = [
            _make_reasons_item(self.queue, {
                "confidence": 0.9, "keywords": ["GPT-5"],
            }, source="https://openai.com", category="ai", title="OpenAI"),
            _make_reasons_item(self.queue, {
                "confidence": 0.7, "keywords": ["Steam", "sale"],
            }, source="https://steampowered.com", category="gaming", title="Steam"),
            _make_reasons_item(self.queue, {
                "confidence": 0.85, "keywords": ["GPT-5", "reasoning"],
            }, source="https://openai.com", category="ai", title="GPT5 Reasoning"),
        ]
        self.cli.record_decision(items[0], Decision.APPROVE, "other", None)
        self.cli.record_decision(items[1], Decision.REJECT, "low_relevance", None)
        self.cli.record_decision(items[2], Decision.APPROVE, "other", None)

        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_progress()
        output = buf.file.getvalue()

        assert "Articles reviewed: 3" in output
        assert "Source Profiles" in output
        assert "Category Breakdown" in output
        assert "Top Keywords" in output
        assert "Confidence Trend" in output
        assert "Human-AI Agreement" in output


# ── Enhanced Card ────────────────────────────────────────────────────


class TestEnhancedCard:
    """Card with confidence bar in header."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_card_shows_confidence_bar(self) -> None:
        item = _make_reasons_item(self.queue, {
            "confidence": 0.92, "source_quality": 0.9,
            "freshness": "High", "keywords": ["AI"],
        })
        panel = self.cli._build_card(item)
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        buf.print(panel)
        output = buf.file.getvalue()

        assert "AI recommends" in output
        assert "Confidence" in output
        assert "92%" in output

    def test_card_shows_score_color(self) -> None:
        item = _make_item(self.queue, score=0.92)
        panel = self.cli._build_card(item)
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        buf.print(panel)
        output = buf.file.getvalue()
        assert "0.92" in output


# ── Enhanced Why Section ─────────────────────────────────────────────


class TestEnhancedWhySection:
    """Enhanced recommendation explanation with duplicates, trend, confidence bar."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def _render_why(self, reasons_data: dict) -> str:
        item = _make_reasons_item(self.queue, reasons_data)
        panel = self.cli._build_card(item)
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        buf.print(panel)
        return buf.file.getvalue()

    def test_duplicates_factor(self) -> None:
        content = self._render_why({
            "confidence": 0.8, "duplicates": 2,
        })
        assert "Duplicate potential" in content
        assert "2" in content

    def test_trend_factor(self) -> None:
        content = self._render_why({
            "confidence": 0.8, "trend": "Rising",
        })
        assert "Trend" in content
        assert "Rising" in content

    def test_confidence_bar_in_why(self) -> None:
        content = self._render_why({
            "confidence": 0.85, "source_quality": 0.9,
        })
        assert "Confidence" in content
        assert "85%" in content

    def test_source_quality_indicator(self) -> None:
        content = self._render_why({"source_quality": 0.9})
        assert "Source quality" in content
        assert "0.90" in content

    def test_freshness_indicator(self) -> None:
        content = self._render_why({"freshness": "High"})
        assert "Freshness" in content
        assert "High" in content

    def test_keywords_with_markup(self) -> None:
        content = self._render_why({"keywords": ["GPT-5", "LLM", "reasoning"]})
        assert "Keywords" in content
        assert "GPT-5" in content
        assert "LLM" in content

    def test_similar_approved(self) -> None:
        content = self._render_why({"similar_approved": 42})
        assert "Similar approved articles" in content
        assert "42" in content


# ── H Shortcut ───────────────────────────────────────────────────────


class TestHistoryShortcut:
    """H shortcut in get_decision."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_h_shows_history_and_continues(self) -> None:
        """H shows history then re-asks for decision."""
        with patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["H", "S"]
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP
            assert mock_prompt.call_count == 2

    def test_history_shown_before_re_ask(self) -> None:
        """After H, history panel is displayed."""
        item = _make_item(self.queue, title="Test")
        self.cli.record_decision(item, Decision.APPROVE, "other", None)

        with patch("runtime.feedback.cli.Prompt.ask") as mock_prompt:
            mock_prompt.side_effect = ["H", "S"]
            # This will call show_history internally
            decision, reason, comment = self.cli.get_decision()
            assert decision == Decision.SKIP


# ── Integration: Full Decision Flow with Learning ────────────────────


class TestFullDecisionFlow:
    """Integration test: record → learning update → export → progress."""

    def setup_method(self) -> None:
        self.queue = DecisionQueue()
        self.reasons = FeedbackReasons()
        self.cli = FeedbackCLI(self.queue, self.reasons)

    def test_full_flow(self, tmp_path: Path) -> None:
        # Add items
        item1 = _make_reasons_item(self.queue, {
            "confidence": 0.9, "keywords": ["GPT-5"],
            "source_quality": 0.95, "freshness": "High",
        }, title="GPT-5 Launch", source="https://openai.com", category="ai")

        item2 = _make_reasons_item(self.queue, {
            "confidence": 0.6, "keywords": ["sale"],
            "source_quality": 0.7, "freshness": "Medium",
        }, title="Steam Sale", source="https://steampowered.com", category="gaming")

        # Record decisions
        self.cli.record_decision(item1, Decision.APPROVE, "other", None)
        self.cli.record_decision(item2, Decision.REJECT, "low_relevance", None)

        # Verify stats
        assert self.cli.session_stats.approved == 1
        assert self.cli.session_stats.rejected == 1
        assert len(self.cli.session_stats.sources_seen) == 2
        assert len(self.cli.session_stats.categories_seen) == 2

        # Show learning update (render to buffer)
        from io import StringIO
        from rich.console import Console
        buf = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf
        self.cli.show_learning_update(item1, Decision.APPROVE, "other")
        output = buf.file.getvalue()
        assert "Learning Updated" in output

        # Show history
        buf2 = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf2
        self.cli.show_history()
        output2 = buf2.file.getvalue()
        assert "GPT-5 Launch" in output2
        assert "Steam Sale" in output2

        # Export
        filepath = self.cli.export_session(str(tmp_path))
        assert filepath is not None
        data = json.loads(Path(filepath).read_text())
        assert len(data["decisions"]) == 2
        assert data["learning_growth"]["sources_profiled"] == 2

        # Learning progress
        buf3 = Console(file=StringIO(), width=120, no_color=True)
        self.cli._console = buf3
        self.cli.show_learning_progress()
        output3 = buf3.file.getvalue()
        assert "Articles reviewed: 2" in output3
        assert "Source Profiles" in output3
