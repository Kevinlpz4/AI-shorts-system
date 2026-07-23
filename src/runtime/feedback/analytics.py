"""
Analytics collector — computes statistics from feedback records.

Design principles:
    1. Pure computation — no side effects, no persistence.
    2. Source filtering uses a minimum threshold for statistical significance.
    3. All time-based queries use local date comparison.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from runtime.feedback.models import Decision, FeedbackRecord


class AnalyticsCollector:
    """Collects and computes analytics from feedback records.

    Records are added via ``add_record()``. All analytics methods
    compute on the in-memory record list.
    """

    MIN_SOURCE_ITEMS = 3

    def __init__(self) -> None:
        self._records: List[FeedbackRecord] = []

    def add_record(self, record: FeedbackRecord) -> None:
        """Add a feedback record to the analytics collector."""
        self._records.append(record)

    def get_approval_rate(self) -> float:
        """Calculate approval rate."""
        if not self._records:
            return 0.0
        approved = len([r for r in self._records if r.decision == Decision.APPROVE])
        return approved / len(self._records)

    def get_rejection_rate(self) -> float:
        """Calculate rejection rate."""
        if not self._records:
            return 0.0
        rejected = len([r for r in self._records if r.decision == Decision.REJECT])
        return rejected / len(self._records)

    def get_top_reasons(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top rejection reasons."""
        reasons = [r.reason for r in self._records if r.decision == Decision.REJECT]
        counter = Counter(reasons)
        return [
            {"reason": reason, "count": count}
            for reason, count in counter.most_common(limit)
        ]

    def get_top_sources(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sources with highest approval rates (min 3 items)."""
        source_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "approved": 0}
        )
        for record in self._records:
            source_stats[record.source]["total"] += 1
            if record.decision == Decision.APPROVE:
                source_stats[record.source]["approved"] += 1

        results = []
        for source, stats in source_stats.items():
            if stats["total"] >= self.MIN_SOURCE_ITEMS:
                rate = stats["approved"] / stats["total"]
                results.append({
                    "source": source,
                    "approval_rate": rate,
                    "total": stats["total"],
                    "approved": stats["approved"],
                })

        results.sort(key=lambda x: x["approval_rate"], reverse=True)
        return results[:limit]

    def get_worst_sources(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sources with lowest approval rates."""
        top = self.get_top_sources(limit=100)
        return list(reversed(top))[:limit]

    def get_category_stats(self) -> List[Dict[str, Any]]:
        """Get approval rates by category."""
        category_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "approved": 0}
        )
        for record in self._records:
            category_stats[record.category]["total"] += 1
            if record.decision == Decision.APPROVE:
                category_stats[record.category]["approved"] += 1

        results = []
        for category, stats in category_stats.items():
            rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0
            results.append({
                "category": category,
                "approval_rate": rate,
                "total": stats["total"],
                "approved": stats["approved"],
            })

        results.sort(key=lambda x: x["approval_rate"], reverse=True)
        return results

    def get_keyword_stats(self) -> List[Dict[str, Any]]:
        """Get approval rates by topic/keyword."""
        topic_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "approved": 0}
        )
        for record in self._records:
            topic_stats[record.topic]["total"] += 1
            if record.decision == Decision.APPROVE:
                topic_stats[record.topic]["approved"] += 1

        results = []
        for topic, stats in topic_stats.items():
            rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0
            results.append({
                "topic": topic,
                "approval_rate": rate,
                "total": stats["total"],
                "approved": stats["approved"],
            })

        results.sort(key=lambda x: x["approval_rate"], reverse=True)
        return results

    def get_daily_evolution(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily approval/rejection evolution."""
        today = datetime.now().date()
        daily_stats = []

        for i in range(days):
            date = today - timedelta(days=i)
            day_records = [
                r for r in self._records if r.timestamp.date() == date
            ]

            if day_records:
                approved = len([r for r in day_records if r.decision == Decision.APPROVE])
                rejected = len([r for r in day_records if r.decision == Decision.REJECT])
                total = len(day_records)
                rate = approved / total if total > 0 else 0

                daily_stats.append({
                    "date": date.isoformat(),
                    "total": total,
                    "approved": approved,
                    "rejected": rejected,
                    "approval_rate": rate,
                })

        return list(reversed(daily_stats))

    def get_weekly_evolution(self, weeks: int = 4) -> List[Dict[str, Any]]:
        """Get weekly approval/rejection evolution."""
        today = datetime.now().date()
        weekly_stats = []

        for i in range(weeks):
            week_start = today - timedelta(days=today.weekday() + (i * 7))
            week_end = week_start + timedelta(days=6)

            week_records = [
                r for r in self._records
                if week_start <= r.timestamp.date() <= week_end
            ]

            if week_records:
                approved = len([r for r in week_records if r.decision == Decision.APPROVE])
                rejected = len([r for r in week_records if r.decision == Decision.REJECT])
                total = len(week_records)
                rate = approved / total if total > 0 else 0

                weekly_stats.append({
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "total": total,
                    "approved": approved,
                    "rejected": rejected,
                    "approval_rate": rate,
                })

        return list(reversed(weekly_stats))

    def get_summary(self) -> Dict[str, Any]:
        """Get complete analytics summary."""
        return {
            "total_records": len(self._records),
            "approval_rate": self.get_approval_rate(),
            "rejection_rate": self.get_rejection_rate(),
            "top_reasons": self.get_top_reasons(),
            "top_sources": self.get_top_sources(),
            "worst_sources": self.get_worst_sources(),
            "category_stats": self.get_category_stats(),
            "keyword_stats": self.get_keyword_stats(),
            "daily_evolution": self.get_daily_evolution(),
            "weekly_evolution": self.get_weekly_evolution(),
        }
