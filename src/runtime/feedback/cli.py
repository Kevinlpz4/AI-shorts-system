"""
Feedback CLI — Rich-based interface for human feedback review.

Design principles:
    1. Pure presentation layer — no business logic.
    2. All I/O goes through Rich Console.
    3. Decision flow: show item → get decision → process → loop.
    4. Shortcuts: A(pprove), R(eject), S(kip), Q(uit), O(pen URL), U(ndo), H(istory)
"""
from __future__ import annotations

import json
import time
import webbrowser
from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime, timezone
import uuid
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from runtime.feedback.models import Decision
from runtime.feedback.queue import DecisionQueue, QueueItem
from runtime.feedback.reasons import FeedbackReasons


def _score_color(score: float) -> str:
    """Return Rich color style for a score value."""
    if score >= 0.80:
        return "green"
    if score >= 0.50:
        return "yellow"
    return "red"


def _confidence_bar(confidence: float, width: int = 12) -> str:
    """Render a visual confidence bar."""
    filled = int(width * confidence)
    empty = width - filled
    color = _score_color(confidence)
    return f"[{color}]{'█' * filled}{'░' * empty}[/{color}] {confidence:.0%}"


@dataclass
class SessionDecision:
    """One decision made during a session — for undo, history, and export."""

    item: QueueItem
    decision: Decision
    reason: str
    comment: Optional[str]
    timestamp: float
    ai_agrees: bool = True

    @property
    def time_str(self) -> str:
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")

    @property
    def title_or_id(self) -> str:
        return self.item.title or self.item.article_id[:12]

    @property
    def icon(self) -> str:
        if self.decision == Decision.APPROVE:
            return "✅"
        if self.decision == Decision.REJECT:
            return "❌"
        return "⏭"

    @property
    def decision_label(self) -> str:
        return self.decision.value.upper()


@dataclass
class SessionStats:
    """Mutable session statistics."""

    total: int = 0
    approved: int = 0
    rejected: int = 0
    skipped: int = 0
    start_time: float = field(default_factory=time.time)
    decision_times: list[float] = field(default_factory=list)
    records_sent: int = 0
    # Learning growth tracking
    sources_seen: dict = field(default_factory=dict)   # source → {approved, rejected}
    categories_seen: dict = field(default_factory=dict) # category → {approved, rejected}
    keywords_seen: dict = field(default_factory=dict)   # keyword → count
    confidence_trend: list[float] = field(default_factory=list)

    @property
    def processed(self) -> int:
        return self.approved + self.rejected + self.skipped

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def avg_time(self) -> float:
        if not self.decision_times:
            return 0.0
        return sum(self.decision_times) / len(self.decision_times)

    @property
    def agreement_rate(self) -> float:
        """Rate at which human agrees with AI recommendation."""
        total_decisions = self.approved + self.rejected
        if total_decisions == 0:
            return 0.0
        # Count agreements: approve when AI said approve, reject when AI said reject
        agreements = sum(
            1 for d in self._decisions_list
            if d.ai_agrees
        )
        return agreements / total_decisions if total_decisions > 0 else 0.0

    def eta_for(self, remaining: int) -> float:
        return self.avg_time * remaining if self.avg_time > 0 else 0.0

    # Internal list of decisions for agreement tracking
    _decisions_list: list = field(default_factory=list, repr=False)

    def record_source(self, source: str, approved: bool) -> None:
        if source not in self.sources_seen:
            self.sources_seen[source] = {"approved": 0, "rejected": 0}
        key = "approved" if approved else "rejected"
        self.sources_seen[source][key] += 1

    def record_category(self, category: str, approved: bool) -> None:
        if category not in self.categories_seen:
            self.categories_seen[category] = {"approved": 0, "rejected": 0}
        key = "approved" if approved else "rejected"
        self.categories_seen[category][key] += 1

    def record_keywords(self, keywords: list[str]) -> None:
        for kw in keywords:
            self.keywords_seen[kw] = self.keywords_seen.get(kw, 0) + 1

    def record_confidence(self, confidence: float) -> None:
        self.confidence_trend.append(confidence)


class FeedbackCLI:
    """Rich-based CLI for human feedback on recommended items.

    Supports shortcuts (A/R/S/Q/O/U/H), progress bar, numbered reason menu,
    undo, session history, learning panels, and JSON export.
    """

    def __init__(self, queue: DecisionQueue, reasons: FeedbackReasons) -> None:
        self._queue = queue
        self._reasons = reasons
        self._console = Console()
        self._user_id = f"user-{uuid.uuid4().hex[:8]}"
        self._session_stats = SessionStats()
        self._undo_stack: list[SessionDecision] = []
        self._last_item: Optional[QueueItem] = None
        self._items_total: int = 0
        self._session_id = str(uuid.uuid4())

    @property
    def session_stats(self) -> SessionStats:
        return self._session_stats

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def session_id(self) -> str:
        return self._session_id

    # ── Progress ─────────────────────────────────────────────────────

    def set_total(self, total: int) -> None:
        """Set total items for progress tracking."""
        self._items_total = total
        self._session_stats.total = total

    def show_progress(self) -> None:
        """Display progress bar with current/total, percentage, avg time, ETA."""
        stats = self._session_stats
        current = stats.processed + 1
        total = self._items_total
        if total == 0:
            return

        pct = (stats.processed / total) * 100
        bar_width = 30
        filled = int(bar_width * stats.processed / total)
        bar = "█" * filled + "░" * (bar_width - filled)

        eta = stats.eta_for(total - stats.processed)
        eta_str = self._format_time(eta) if eta > 0 else "--:--"
        avg_str = self._format_time(stats.avg_time) if stats.avg_time > 0 else "--:--"

        progress = (
            f"[cyan]{current}[/cyan]/[bold]{total}[/bold] "
            f"({pct:.0f}%) "
            f"[{bar}] "
            f"Avg: {avg_str} "
            f"ETA: {eta_str}"
        )
        self._console.print(progress)

    def _format_time(self, seconds: float) -> str:
        """Format seconds as M:SS."""
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    # ── Display ──────────────────────────────────────────────────────

    def show_next_item(self) -> Optional[dict]:
        """Display the next pending item. Returns item info or None."""
        result = self._queue.get_next()
        if result.is_failure or result.value is None:
            return None

        item = result.value
        self._last_item = item
        panel = self._build_card(item)
        self._console.print(panel)
        return {"item": item, "id": item.id}

    def _build_card(self, item: QueueItem) -> Panel:
        """Build a Rich Panel with full item context."""
        sections: list[str] = []

        # ── AI Recommendation header ────────────────────────────
        rec_style = "green" if item.recommendation.upper() == "APPROVE" else "red"
        confidence = item.metadata.get("reasons", {}).get("confidence", item.score)
        conf_bar = _confidence_bar(float(confidence))

        sections.append(
            f"[bold {rec_style}]► AI recommends: {item.recommendation}[/bold {rec_style}]"
            f"  Confidence: {conf_bar}"
        )

        # ── Title ────────────────────────────────────────────────
        if item.title:
            sections.append(f"\n[bold white]{item.title}[/bold white]")

        # ── Summary ──────────────────────────────────────────────
        summary = item.summary or item.metadata.get("summary", "")
        if summary:
            sections.append(f"\n{summary}")

        # ── Metadata grid ────────────────────────────────────────
        meta_lines: list[str] = []
        meta_lines.append(self._meta_row("Provider", item.provider))
        meta_lines.append(self._meta_row("Source", item.source))

        if item.published:
            meta_lines.append(self._meta_row("Published", item.published))

        meta_lines.append(self._meta_row("Category", item.category))
        meta_lines.append(self._meta_row("Topic", item.topic))

        # Score with color
        color = _score_color(item.score)
        meta_lines.append(
            f"  [bold]Score:[/bold]         [{color}]{item.score:.2f}[/{color}]"
        )

        meta_lines.append(self._meta_row("Recommendation", item.recommendation))
        sections.append("\n" + "\n".join(meta_lines))

        # ── URL ──────────────────────────────────────────────────
        url = item.url or item.metadata.get("url", "")
        if url:
            sections.append(f"\n[dim]{url}[/dim]")

        # ── Why this recommendation? ─────────────────────────────
        why = self._build_why_section(item)
        if why:
            sections.append(f"\n{why}")

        # ── ID footer ────────────────────────────────────────────
        sections.append(f"\n[dim]ID: {item.id[:8]}[/dim]")

        return Panel(
            "\n".join(sections),
            title=f"[bold]Pending Item #{item.id[:8]}[/bold]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _meta_row(self, label: str, value: str) -> str:
        """Format a metadata row with consistent alignment."""
        return f"  [bold]{label}:[/bold]         {value}"

    def _build_why_section(self, item: QueueItem) -> str:
        """Build the 'Why this recommendation?' section with enhanced factor breakdown."""
        reasons_data = item.metadata.get("reasons", item.metadata.get("why", {}))
        if not reasons_data or not isinstance(reasons_data, dict):
            return ""

        lines: list[str] = ["[bold cyan]Why this recommendation?[/bold cyan]"]

        # Source quality
        source_quality = reasons_data.get("source_quality")
        if source_quality is not None:
            sq = float(source_quality)
            color = _score_color(sq)
            indicator = "✓" if sq >= 0.7 else "⚠" if sq >= 0.4 else "✗"
            lines.append(
                f"  [{color}]{indicator}[/{color}] Source quality: "
                f"[{color}]{sq:.2f}[/{color}]"
            )

        # Freshness
        freshness = reasons_data.get("freshness")
        if freshness is not None:
            freshness_label = str(freshness)
            fresh_color = "green" if freshness_label.lower() in ("high", "very high") else (
                "yellow" if freshness_label.lower() == "medium" else "red"
            )
            indicator = "✓" if fresh_color == "green" else "⚠" if fresh_color == "yellow" else "✗"
            lines.append(
                f"  [{fresh_color}]{indicator}[/{fresh_color}] Freshness: "
                f"[{fresh_color}]{freshness_label}[/{fresh_color}]"
            )

        # Keywords
        keywords = reasons_data.get("keywords")
        if keywords:
            kw_list = keywords if isinstance(keywords, list) else [keywords]
            kw_str = ", ".join(f"[cyan]{k}[/cyan]" for k in kw_list[:5])
            lines.append(f"  [green]✓[/green] Keywords: {kw_str}")

        # Similar approved
        similar = reasons_data.get("similar_approved")
        if similar is not None:
            sim_val = int(similar)
            sim_color = "green" if sim_val >= 20 else "yellow" if sim_val >= 5 else "red"
            lines.append(
                f"  [{sim_color}]✓[/{sim_color}] Similar approved articles: {sim_val}"
            )

        # Duplicates check
        duplicates = reasons_data.get("duplicates")
        if duplicates is not None:
            dup_val = int(duplicates)
            dup_color = "red" if dup_val > 0 else "green"
            lines.append(
                f"  [{dup_color}]{'⚠' if dup_val > 0 else '✓'}[/{dup_color}] "
                f"Duplicate potential: {dup_val}"
            )

        # Trend
        trend = reasons_data.get("trend")
        if trend is not None:
            trend_label = str(trend)
            trend_color = "green" if "up" in trend_label.lower() else (
                "yellow" if "stable" in trend_label.lower() else "red"
            )
            lines.append(
                f"  [{trend_color}]✓[/{trend_color}] Trend: {trend_label}"
            )

        # Confidence
        confidence = reasons_data.get("confidence")
        if confidence is not None:
            cf = float(confidence)
            color = _score_color(cf)
            lines.append(
                f"  [green]✓[/green] Confidence: "
                f"[{color}]{_confidence_bar(cf)}[/{color}]"
            )

        return "\n".join(lines)

    # ── Shortcuts display ───────────────────────────────────────────

    def _show_shortcuts(self) -> None:
        """Show available keyboard shortcuts."""
        self._console.print(
            "[dim]  [A]pprove  [R]eject  [S]kip  [Q]uit  "
            "[O]pen URL  [U]ndo  [H]istory[/dim]"
        )

    # ── Decision ─────────────────────────────────────────────────────

    def get_decision(self) -> Tuple[Decision, str, Optional[str]]:
        """Get decision from user via shortcuts or numbered menu.

        Returns (decision, reason_code, comment).
        Special return: Decision.SKIP with reason "quit" means user wants to quit.
        Special return: Decision.SKIP with reason "history" means user wants to see history.
        """
        self._show_shortcuts()

        while True:
            raw = Prompt.ask("[bold]Action[/bold]").strip().upper()

            # ── Shortcuts ────────────────────────────────────────
            if raw in ("A", "APPROVE"):
                return Decision.APPROVE, "other", None

            if raw in ("R", "REJECT"):
                reason_code = self._select_reason_numbered()
                comment = None
                if reason_code == "other":
                    comment = Prompt.ask("  [dim]Enter comment[/dim]")
                return Decision.REJECT, reason_code, comment

            if raw in ("S", "SKIP"):
                return Decision.SKIP, "other", None

            if raw in ("Q", "QUIT"):
                return Decision.SKIP, "quit", None

            if raw in ("O", "OPEN"):
                self._open_url()
                continue  # After opening, ask again

            if raw in ("U", "UNDO"):
                self._undo_last()
                continue  # After undo, re-show item

            if raw in ("H", "HISTORY"):
                self.show_history()
                continue  # After showing history, ask again

            # ── Legacy numbered menu ─────────────────────────────
            if raw in ("1", "2", "3"):
                return self._handle_numbered_choice(int(raw))

            self._console.print(
                "[yellow]  Unknown command. Use A/R/S/Q/O/U/H or 1/2/3[/yellow]"
            )

    def _handle_numbered_choice(self, choice: int) -> Tuple[Decision, str, Optional[str]]:
        """Handle legacy 1/2/3 numbered choices."""
        decision_map = {
            1: Decision.APPROVE,
            2: Decision.REJECT,
            3: Decision.SKIP,
        }
        decision = decision_map[choice]
        reason_code = "other"
        comment = None

        if decision == Decision.REJECT:
            reason_code = self._select_reason_numbered()
            if reason_code == "other":
                comment = Prompt.ask("  [dim]Enter comment[/dim]")

        return decision, reason_code, comment

    def _select_reason_numbered(self) -> str:
        """Select a rejection reason via numbered menu."""
        reasons = self._reasons.list_all()

        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Num", style="cyan", width=3)
        table.add_column("Label", style="white")

        for i, reason in enumerate(reasons, 1):
            table.add_row(f"{i}.", reason.label)

        self._console.print(table)

        codes = [r.code for r in reasons]
        valid_choices = [str(i) for i in range(1, len(reasons) + 1)]

        while True:
            raw = Prompt.ask("  [dim]Reason number[/dim]", choices=valid_choices)
            idx = int(raw) - 1
            return codes[idx]

    # ── Undo ─────────────────────────────────────────────────────────

    def _undo_last(self) -> None:
        """Undo the last decision — re-queue the item."""
        if not self._undo_stack:
            self._console.print("[yellow]  Nothing to undo.[/yellow]")
            return

        last = self._undo_stack.pop()
        # Re-add to queue
        self._queue.add(
            article_id=last.item.article_id,
            provider=last.item.provider,
            source=last.item.source,
            category=last.item.category,
            topic=last.item.topic,
            score=last.item.score,
            recommendation=last.item.recommendation,
            metadata=last.item.metadata,
            title=last.item.title,
            url=last.item.url,
            published=last.item.published,
            summary=last.item.summary,
        )
        # Restore item id so it's the same item
        re_added = self._queue.get_next()
        if re_added.is_success and re_added.value:
            re_added.value.id = last.item.id

        # Update stats
        if last.decision == Decision.APPROVE:
            self._session_stats.approved -= 1
        elif last.decision == Decision.REJECT:
            self._session_stats.rejected -= 1
        elif last.decision == Decision.SKIP:
            self._session_stats.skipped -= 1

        self._console.print(
            f"[green]  ↩ Undone: {last.item.title or last.item.article_id}[/green]"
        )

    def record_decision(
        self, item: QueueItem, decision: Decision, reason: str, comment: Optional[str],
    ) -> None:
        """Record a decision for undo, stats, and learning tracking."""
        self._session_stats.decision_times.append(time.time())

        if decision == Decision.APPROVE:
            self._session_stats.approved += 1
        elif decision == Decision.REJECT:
            self._session_stats.rejected += 1
        elif decision == Decision.SKIP:
            self._session_stats.skipped += 1

        # Check if human agrees with AI
        ai_agrees = decision.value.upper() == item.recommendation.upper()

        session_decision = SessionDecision(
            item=item,
            decision=decision,
            reason=reason,
            comment=comment,
            timestamp=time.time(),
            ai_agrees=ai_agrees,
        )

        self._undo_stack.append(session_decision)
        self._session_stats._decisions_list.append(session_decision)

        # Track learning growth
        approved = decision == Decision.APPROVE
        self._session_stats.record_source(item.source, approved)
        self._session_stats.record_category(item.category, approved)

        reasons_data = item.metadata.get("reasons", {})
        keywords = reasons_data.get("keywords", [])
        if isinstance(keywords, list):
            self._session_stats.record_keywords(keywords)

        confidence = reasons_data.get("confidence", item.score)
        self._session_stats.record_confidence(float(confidence))

    # ── Learning Updated Panel ───────────────────────────────────────

    def show_learning_update(
        self, item: QueueItem, decision: Decision, reason: str,
    ) -> None:
        """Show how the system's learning profile changes after a decision."""
        reasons_data = item.metadata.get("reasons", {})
        source = item.source
        category = item.category
        keywords = reasons_data.get("keywords", [])
        confidence = float(reasons_data.get("confidence", item.score))

        approved = decision == Decision.APPROVE
        stats = self._session_stats

        # Build source profile update
        source_stats = stats.sources_seen.get(source, {"approved": 0, "rejected": 0})
        total_source = source_stats["approved"] + source_stats["rejected"]
        source_rate = (
            source_stats["approved"] / total_source if total_source > 0 else 0.0
        )

        # Build category profile update
        cat_stats = stats.categories_seen.get(category, {"approved": 0, "rejected": 0})
        total_cat = cat_stats["approved"] + cat_stats["rejected"]
        cat_rate = cat_stats["approved"] / total_cat if total_cat > 0 else 0.0

        # Build confidence trend
        trend = stats.confidence_trend
        avg_confidence = sum(trend) / len(trend) if trend else confidence
        trend_direction = "→ stable"
        if len(trend) >= 2:
            if trend[-1] > trend[-2]:
                trend_direction = "↗ rising"
            elif trend[-1] < trend[-2]:
                trend_direction = "↘ falling"

        # Build panel content
        lines: list[str] = []

        # Source profile
        source_color = _score_color(source_rate)
        lines.append(
            f"  [bold]Source profile:[/bold] {source}\n"
            f"    Approval rate: [{source_color}]{source_rate:.0%}[/{source_color}] "
            f"({source_stats['approved']}A / {source_stats['rejected']}R from {total_source} reviews)"
        )

        # Category profile
        cat_color = _score_color(cat_rate)
        lines.append(
            f"  [bold]Category:[/bold] {category}\n"
            f"    Approval rate: [{cat_color}]{cat_rate:.0%}[/{cat_color}] "
            f"({cat_stats['approved']}A / {cat_stats['rejected']}R)"
        )

        # Keywords update
        if keywords:
            kw_display = ", ".join(f"[cyan]{k}[/cyan]" for k in keywords[:4])
            kw_freq = stats.keywords_seen.get(keywords[0], 1) if keywords else 0
            lines.append(
                f"  [bold]Keywords:[/bold] {kw_display}\n"
                f"    Frequency: {kw_freq}x seen"
            )

        # Confidence trend
        conf_color = _score_color(avg_confidence)
        lines.append(
            f"  [bold]Confidence:[/bold] "
            f"[{conf_color}]{_confidence_bar(avg_confidence)}[/{conf_color}] "
            f"{trend_direction}"
        )

        # Decision impact
        impact = "✓ Reinforces" if approved else "✗ Penalizes"
        impact_color = "green" if approved else "red"
        lines.append(
            f"\n  [{impact_color}]{impact}[/{impact_color}] "
            f"{category}/{source} profile"
        )

        panel = Panel(
            "\n".join(lines),
            title="[bold magenta]📚 Learning Updated[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        self._console.print(panel)

    # ── Session History ──────────────────────────────────────────────

    def show_history(self, last_n: int = 10) -> None:
        """Show the last N decisions made in this session."""
        decisions = self._undo_stack

        if not decisions:
            self._console.print(
                Panel(
                    "[dim]No decisions made yet in this session.[/dim]",
                    title="[bold]📋 Session History[/bold]",
                    border_style="dim",
                )
            )
            return

        recent = decisions[-last_n:]

        table = Table(
            title=f"📋 Session History (last {len(recent)} of {len(decisions)})",
            box=box.ROUNDED,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Decision", width=10)
        table.add_column("Title", max_width=40)
        table.add_column("Source", max_width=20)
        table.add_column("Score", width=6)
        table.add_column("Agree", width=5)

        for i, sd in enumerate(recent, 1):
            dec_color = "green" if sd.decision == Decision.APPROVE else (
                "red" if sd.decision == Decision.REJECT else "yellow"
            )
            agree_mark = "[green]✓[/green]" if sd.ai_agrees else "[red]✗[/red]"
            score_color = _score_color(sd.item.score)

            table.add_row(
                str(i),
                sd.time_str,
                f"[{dec_color}]{sd.decision_label}[/{dec_color}]",
                sd.title_or_id[:40],
                sd.item.source[:20],
                f"[{score_color}]{sd.item.score:.2f}[/{score_color}]",
                agree_mark,
            )

        self._console.print(table)

        # Undo info
        self._console.print(
            f"  [dim]Type [U]ndo to revert the last decision "
            f"({len(self._undo_stack)} in stack)[/dim]"
        )

    # ── Open URL ─────────────────────────────────────────────────────

    def _open_url(self) -> None:
        """Open the current item's URL in the system browser."""
        if not self._last_item:
            self._console.print("[yellow]  No item to open.[/yellow]")
            return

        url = self._last_item.url or self._last_item.metadata.get("url", "")
        if not url:
            self._console.print("[yellow]  No URL available for this item.[/yellow]")
            return

        try:
            webbrowser.open(url)
            self._console.print(f"[green]  🔗 Opened: {url}[/green]")
        except Exception as exc:
            self._console.print(f"[red]  Failed to open URL: {exc}[/red]")

    # ── Recommendation vs Decision ───────────────────────────────────

    def show_decision_diff(self, item: QueueItem, decision: Decision) -> None:
        """Show when human decision differs from system recommendation."""
        sys_rec = item.recommendation.upper()
        human = decision.value.upper()

        if sys_rec == human:
            return

        rec_color = "green" if sys_rec == "APPROVE" else "red"
        dec_color = "green" if human == "APPROVE" else "red"

        self._console.print(
            f"  [bold]System:[/bold] [{rec_color}]{sys_rec}[/{rec_color}]  "
            f"→  [bold]You:[/bold] [{dec_color}]{human}[/{dec_color}]"
        )

    # ── JSON Session Export ──────────────────────────────────────────

    def export_session(self, output_dir: str = ".") -> Optional[str]:
        """Export session data to a JSON file.

        Returns the file path if successful, None otherwise.
        """
        stats = self._session_stats
        export_data = {
            "session": {
                "id": self._session_id,
                "user_id": self._user_id,
                "started_at": datetime.fromtimestamp(
                    stats.start_time, tz=timezone.utc
                ).isoformat(),
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": stats.elapsed,
            },
            "statistics": {
                "total_items": stats.total,
                "approved": stats.approved,
                "rejected": stats.rejected,
                "skipped": stats.skipped,
                "processed": stats.processed,
                "approval_rate": (
                    stats.approved / stats.processed if stats.processed > 0 else 0.0
                ),
                "avg_decision_time": stats.avg_time,
                "agreement_rate": stats.agreement_rate,
                "records_sent": stats.records_sent,
            },
            "learning_growth": {
                "sources_profiled": len(stats.sources_seen),
                "categories_profiled": len(stats.categories_seen),
                "unique_keywords": len(stats.keywords_seen),
                "top_keywords": sorted(
                    stats.keywords_seen.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "confidence_trend": stats.confidence_trend,
                "avg_confidence": (
                    sum(stats.confidence_trend) / len(stats.confidence_trend)
                    if stats.confidence_trend
                    else 0.0
                ),
            },
            "decisions": [],
        }

        # Export each decision
        for sd in self._undo_stack:
            decision_entry = {
                "timestamp": datetime.fromtimestamp(
                    sd.timestamp, tz=timezone.utc
                ).isoformat(),
                "decision": sd.decision.value,
                "reason": sd.reason,
                "comment": sd.comment,
                "ai_agrees": sd.ai_agrees,
                "item": {
                    "id": sd.item.id,
                    "article_id": sd.item.article_id,
                    "title": sd.item.title,
                    "url": sd.item.url,
                    "provider": sd.item.provider,
                    "source": sd.item.source,
                    "category": sd.item.category,
                    "topic": sd.item.topic,
                    "score": sd.item.score,
                    "recommendation": sd.item.recommendation,
                },
            }
            export_data["decisions"].append(decision_entry)

        # Write to file
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_session_{timestamp_str}.json"
        filepath = Path(output_dir) / filename

        try:
            filepath.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
            return str(filepath)
        except Exception as exc:
            self._console.print(f"[red]  Export failed: {exc}[/red]")
            return None

    # ── Learning Progress Panel ──────────────────────────────────────

    def show_learning_progress(self) -> None:
        """Show final Learning Progress panel — growth of system knowledge."""
        stats = self._session_stats

        lines: list[str] = []

        # ── Knowledge Growth ─────────────────────────────────────
        lines.append("[bold]🧠 Knowledge Growth[/bold]")
        lines.append(f"  Articles reviewed: [cyan]{stats.processed}[/cyan]")
        lines.append(f"  Source profiles: [cyan]{len(stats.sources_seen)}[/cyan]")
        lines.append(f"  Category profiles: [cyan]{len(stats.categories_seen)}[/cyan]")
        lines.append(f"  Keywords learned: [cyan]{len(stats.keywords_seen)}[/cyan]")
        lines.append("")

        # ── Source Profiles ──────────────────────────────────────
        if stats.sources_seen:
            lines.append("[bold]📊 Source Profiles[/bold]")
            for source, s_stats in sorted(
                stats.sources_seen.items(),
                key=lambda x: x[1]["approved"] / max(x[1]["approved"] + x[1]["rejected"], 1),
                reverse=True,
            ):
                total = s_stats["approved"] + s_stats["rejected"]
                rate = s_stats["approved"] / total if total > 0 else 0.0
                color = _score_color(rate)
                bar = _confidence_bar(rate)
                lines.append(
                    f"  [{color}]●[/{color}] {source[:30]:<30} "
                    f"[{color}]{rate:.0%}[/{color}] "
                    f"({s_stats['approved']}A/{s_stats['rejected']}R)"
                )
            lines.append("")

        # ── Category Breakdown ───────────────────────────────────
        if stats.categories_seen:
            lines.append("[bold]📂 Category Breakdown[/bold]")
            for cat, c_stats in sorted(
                stats.categories_seen.items(),
                key=lambda x: x[1]["approved"] / max(x[1]["approved"] + x[1]["rejected"], 1),
                reverse=True,
            ):
                total = c_stats["approved"] + c_stats["rejected"]
                rate = c_stats["approved"] / total if total > 0 else 0.0
                color = _score_color(rate)
                lines.append(
                    f"  [{color}]●[/{color}] {cat:<20} "
                    f"[{color}]{rate:.0%}[/{color}] "
                    f"({c_stats['approved']}A/{c_stats['rejected']}R)"
                )
            lines.append("")

        # ── Top Keywords ─────────────────────────────────────────
        if stats.keywords_seen:
            lines.append("[bold]🔑 Top Keywords Learned[/bold]")
            top_kw = sorted(stats.keywords_seen.items(), key=lambda x: x[1], reverse=True)[:8]
            for kw, count in top_kw:
                bar_len = min(count, 20)
                bar = "█" * bar_len
                lines.append(f"  [cyan]{kw:<20}[/cyan] {bar} ({count}x)")
            lines.append("")

        # ── Confidence Trend ─────────────────────────────────────
        if stats.confidence_trend:
            avg_conf = sum(stats.confidence_trend) / len(stats.confidence_trend)
            min_conf = min(stats.confidence_trend)
            max_conf = max(stats.confidence_trend)
            trend_color = _score_color(avg_conf)

            lines.append("[bold]📈 Confidence Trend[/bold]")
            lines.append(
                f"  Average: [{trend_color}]{_confidence_bar(avg_conf)}[/{trend_color}]"
            )
            lines.append(f"  Range: [{_score_color(min_conf)}]{min_conf:.2f}[/{_score_color(min_conf)}] "
                         f"→ [{_score_color(max_conf)}]{max_conf:.2f}[/{_score_color(max_conf)}]")
            lines.append(f"  Samples: {len(stats.confidence_trend)}")
            lines.append("")

        # ── Agreement Summary ────────────────────────────────────
        if stats.processed > 0:
            agree_rate = stats.agreement_rate
            agree_color = "green" if agree_rate >= 0.7 else "yellow" if agree_rate >= 0.4 else "red"
            lines.append("[bold]🤝 Human-AI Agreement[/bold]")
            lines.append(
                f"  Agreement rate: [{agree_color}]{agree_rate:.0%}[/{agree_color}] "
                f"({stats.approved + stats.rejected} decisions)"
            )

        panel = Panel(
            "\n".join(lines),
            title="[bold green]🌱 Learning Progress — Session Complete[/bold green]",
            border_style="green",
            box=box.DOUBLE,
            padding=(1, 2),
        )
        self._console.print(panel)

    # ── Session Summary ──────────────────────────────────────────────

    def show_session_summary(
        self,
        analytics_summary: dict,
        records_sent: int,
    ) -> None:
        """Display extended session summary with all stats."""
        stats = self._session_stats

        # ── Header ───────────────────────────────────────────────
        self._console.print()
        self._console.print(Panel(
            "[bold]Session Complete[/bold]",
            border_style="green",
            box=box.DOUBLE,
        ))

        # ── Session stats ────────────────────────────────────────
        table = Table(title="Session Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total items", str(stats.total))
        table.add_row("Approved", f"[green]{stats.approved}[/green]")
        table.add_row("Rejected", f"[red]{stats.rejected}[/red]")
        table.add_row("Skipped", f"[yellow]{stats.skipped}[/yellow]")
        table.add_row("Pending (unsynced)", str(stats.total - stats.processed))

        total_time = stats.elapsed
        table.add_row("Total time", self._format_time(total_time))
        table.add_row(
            "Avg time/decision",
            self._format_time(stats.avg_time) if stats.avg_time > 0 else "N/A",
        )
        table.add_row("FeedbackRecords sent", str(records_sent))

        # Agreement rate
        if stats.processed > 0:
            agree_rate = stats.agreement_rate
            agree_color = "green" if agree_rate >= 0.7 else "yellow" if agree_rate >= 0.4 else "red"
            table.add_row(
                "Human-AI agreement",
                f"[{agree_color}]{agree_rate:.0%}[/{agree_color}]",
            )

        self._console.print(table)

        # ── Provider & Category breakdown ────────────────────────
        cat_stats = analytics_summary.get("category_stats", [])
        if cat_stats:
            best_cat = max(cat_stats, key=lambda c: c["approval_rate"])
            worst_cat = min(cat_stats, key=lambda c: c["approval_rate"])

            breakdown = Table(title="Provider & Category Insights", box=box.ROUNDED)
            breakdown.add_column("Metric", style="cyan")
            breakdown.add_column("Value", style="white")

            if best_cat["total"] > 0:
                breakdown.add_row(
                    "Highest approval category",
                    f"{best_cat['category']} ({best_cat['approval_rate']:.0%})",
                )
            if worst_cat["total"] > 0:
                breakdown.add_row(
                    "Lowest approval category",
                    f"{worst_cat['category']} ({worst_cat['approval_rate']:.0%})",
                )

            self._console.print(breakdown)

        # ── Top rejection reasons ────────────────────────────────
        top_reasons = analytics_summary.get("top_reasons", [])
        if top_reasons:
            reasons_table = Table(title="Top Rejection Reasons", box=box.ROUNDED)
            reasons_table.add_column("Reason", style="red")
            reasons_table.add_column("Count", style="yellow")

            for r in top_reasons:
                reasons_table.add_row(r["reason"], str(r["count"]))

            self._console.print(reasons_table)

        # ── Approval rate ────────────────────────────────────────
        if stats.processed > 0:
            rate = stats.approved / stats.processed
            color = "green" if rate >= 0.6 else "yellow" if rate >= 0.4 else "red"
            self._console.print(
                f"\n  [bold]Approval rate:[/bold] [{color}]{rate:.0%}[/{color}] "
                f"({stats.approved}/{stats.processed})"
            )

    # ── Stats & Analytics (kept for backward compat) ─────────────────

    def show_stats(self, stats: dict) -> None:
        """Display queue statistics."""
        table = Table(title="Queue Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Pending", str(stats["pending"]))
        table.add_row("Approved", str(stats["approved"]))
        table.add_row("Rejected", str(stats["rejected"]))
        table.add_row("Skipped", str(stats["skipped"]))
        table.add_row("Total", str(stats["total"]))

        self._console.print(table)

    def show_analytics(self, analytics: dict) -> None:
        """Display analytics summary."""
        table = Table(title="Analytics Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Records", str(analytics["total_records"]))
        table.add_row("Approval Rate", f"{analytics['approval_rate']:.1%}")
        table.add_row("Rejection Rate", f"{analytics['rejection_rate']:.1%}")

        self._console.print(table)

        if analytics.get("top_reasons"):
            reasons_table = Table(title="Top Rejection Reasons", box=box.ROUNDED)
            reasons_table.add_column("Reason", style="red")
            reasons_table.add_column("Count", style="yellow")

            for r in analytics["top_reasons"]:
                reasons_table.add_row(r["reason"], str(r["count"]))

            self._console.print(reasons_table)

        if analytics.get("top_sources"):
            sources_table = Table(title="Top Sources", box=box.ROUNDED)
            sources_table.add_column("Source", style="cyan")
            sources_table.add_column("Approval Rate", style="green")

            for s in analytics["top_sources"]:
                sources_table.add_row(s["source"], f"{s['approval_rate']:.1%}")

            self._console.print(sources_table)
