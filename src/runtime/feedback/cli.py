"""
Feedback CLI — Rich-based interface for human feedback review.

Design principles:
    1. Pure presentation layer — no business logic.
    2. All I/O goes through Rich Console.
    3. Decision flow: show item → get decision → process → loop.
"""
from __future__ import annotations

from typing import Optional, Tuple
from datetime import datetime, timezone
import uuid

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from foundation.result.result import Result
from runtime.feedback.models import Decision
from runtime.feedback.queue import DecisionQueue
from runtime.feedback.reasons import FeedbackReasons


class FeedbackCLI:
    """Rich-based CLI for human feedback on recommended items."""

    def __init__(self, queue: DecisionQueue, reasons: FeedbackReasons) -> None:
        self._queue = queue
        self._reasons = reasons
        self._console = Console()
        self._user_id = f"user-{uuid.uuid4().hex[:8]}"

    def show_next_item(self) -> Optional[dict]:
        """Display the next pending item. Returns item info or None."""
        result = self._queue.get_next()
        if result.is_failure or result.value is None:
            self._console.print("[yellow]No pending items in queue.[/yellow]")
            return None

        item = result.value
        panel = Panel(
            f"[bold]ID:[/bold] {item.id}\n"
            f"[bold]Provider:[/bold] {item.provider}\n"
            f"[bold]Source:[/bold] {item.source}\n"
            f"[bold]Category:[/bold] {item.category}\n"
            f"[bold]Topic:[/bold] {item.topic}\n"
            f"[bold]Score:[/bold] {item.score:.2f}\n"
            f"[bold]Recommendation:[/bold] {item.recommendation}",
            title=f"Pending Item #{item.id[:8]}",
            border_style="blue",
        )
        self._console.print(panel)
        return {"item": item, "id": item.id}

    def get_decision(self) -> Tuple[Decision, str, Optional[str]]:
        """Get decision from user. Returns (decision, reason_code, comment)."""
        self._console.print("\n[bold]Decision:[/bold]")
        self._console.print("  [green]1. Approve[/green]")
        self._console.print("  [red]2. Reject[/red]")
        self._console.print("  [yellow]3. Skip[/yellow]")

        choice = IntPrompt.ask("Enter choice", choices=["1", "2", "3"])

        decision_map = {
            1: Decision.APPROVE,
            2: Decision.REJECT,
            3: Decision.SKIP,
        }

        decision = decision_map[choice]
        reason_code = "other"
        comment = None

        if decision == Decision.REJECT:
            reason_code = self._select_reason()
            if reason_code == "other":
                comment = Prompt.ask("Enter comment")

        return decision, reason_code, comment

    def _select_reason(self) -> str:
        """Select a rejection reason from the catalog."""
        reasons = self._reasons.list_all()

        table = Table(title="Rejection Reasons", box=box.ROUNDED)
        table.add_column("Code", style="cyan")
        table.add_column("Label", style="white")

        for reason in reasons:
            table.add_row(reason.code, reason.label)

        self._console.print(table)

        codes = [r.code for r in reasons]
        choice = Prompt.ask("Enter reason code", choices=codes)
        return choice

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
