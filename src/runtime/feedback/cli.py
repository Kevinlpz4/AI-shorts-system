"""
Feedback CLI — Rich-based interface for human feedback review.

Design principles:
    1. Pure presentation layer — no business logic.
    2. All I/O goes through Rich Console.
    3. Decision flow: show item → get decision → process → loop.
    4. Shortcuts: A(pprove), R(eject), S(kip), Q(uit), O(pen URL), U(ndo)
"""
from __future__ import annotations

import time
import webbrowser
from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime, timezone
import uuid

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from foundation.result.result import Result
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


@dataclass
class SessionDecision:
    """One decision made during a session — for undo and summary."""

    item: QueueItem
    decision: Decision
    reason: str
    comment: Optional[str]
    timestamp: float


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

    def eta_for(self, remaining: int) -> float:
        return self.avg_time * remaining if self.avg_time > 0 else 0.0


class FeedbackCLI:
    """Rich-based CLI for human feedback on recommended items.

    Supports shortcuts (A/R/S/Q/O/U), progress bar, numbered reason menu,
    undo, and extended session summary.
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

    @property
    def session_stats(self) -> SessionStats:
        return self._session_stats

    @property
    def user_id(self) -> str:
        return self._user_id

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

        # ── Recommendation header ────────────────────────────────
        rec_style = "green" if item.recommendation.upper() == "APPROVE" else "red"
        sections.append(
            f"[bold {rec_style}]► {item.recommendation}[/bold {rec_style}]"
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
        """Build the 'Why this recommendation?' section from metadata."""
        reasons_data = item.metadata.get("reasons", item.metadata.get("why", {}))
        if not reasons_data or not isinstance(reasons_data, dict):
            return ""

        lines: list[str] = ["[bold cyan]Why this recommendation?[/bold cyan]"]

        source_quality = reasons_data.get("source_quality")
        if source_quality is not None:
            color = _score_color(float(source_quality))
            lines.append(
                f"  [green]✓[/green] Source quality: "
                f"[{color}]{float(source_quality):.2f}[/{color}]"
            )

        freshness = reasons_data.get("freshness")
        if freshness is not None:
            freshness_label = str(freshness)
            fresh_color = "green" if freshness_label.lower() in ("high", "very high") else (
                "yellow" if freshness_label.lower() == "medium" else "red"
            )
            lines.append(
                f"  [green]✓[/green] Freshness: [{fresh_color}]{freshness_label}[/{fresh_color}]"
            )

        keywords = reasons_data.get("keywords")
        if keywords:
            kw_list = keywords if isinstance(keywords, list) else [keywords]
            kw_str = ", ".join(str(k) for k in kw_list[:5])
            lines.append(f"  [green]✓[/green] Keywords: {kw_str}")

        similar = reasons_data.get("similar_approved")
        if similar is not None:
            lines.append(f"  [green]✓[/green] Similar approved articles: {similar}")

        confidence = reasons_data.get("confidence")
        if confidence is not None:
            color = _score_color(float(confidence))
            lines.append(
                f"  [green]✓[/green] Confidence: "
                f"[{color}]{float(confidence):.2f}[/{color}]"
            )

        return "\n".join(lines)

    # ── Shortcuts display ───────────────────────────────────────────

    def _show_shortcuts(self) -> None:
        """Show available keyboard shortcuts."""
        self._console.print(
            "[dim]  [A]pprove  [R]eject  [S]kip  [Q]uit  "
            "[O]pen URL  [U]ndo[/dim]"
        )

    # ── Decision ─────────────────────────────────────────────────────

    def get_decision(self) -> Tuple[Decision, str, Optional[str]]:
        """Get decision from user via shortcuts or numbered menu.

        Returns (decision, reason_code, comment).
        Special return: Decision.SKIP with reason "quit" means user wants to quit.
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

            # ── Legacy numbered menu ─────────────────────────────
            if raw in ("1", "2", "3"):
                return self._handle_numbered_choice(int(raw))

            self._console.print(
                "[yellow]  Unknown command. Use A/R/S/Q/O/U or 1/2/3[/yellow]"
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
        """Record a decision for undo and stats tracking."""
        elapsed = time.time() - self._session_stats.start_time
        self._session_stats.decision_times.append(time.time())

        if decision == Decision.APPROVE:
            self._session_stats.approved += 1
        elif decision == Decision.REJECT:
            self._session_stats.rejected += 1
        elif decision == Decision.SKIP:
            self._session_stats.skipped += 1

        self._undo_stack.append(SessionDecision(
            item=item,
            decision=decision,
            reason=reason,
            comment=comment,
            timestamp=time.time(),
        ))

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
