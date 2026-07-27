"""
Simulation Metrics — tracks all evolution metrics during simulation.

Records the full lifecycle: source quality, keyword frequency, category preference,
confidence, recommendation score, historical success, learning signals, dataset growth.
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MetricSnapshot:
    """Point-in-time snapshot of simulation metrics."""

    timestamp: datetime
    day: int
    iteration: int
    # Core metrics
    total_articles: int = 0
    total_decisions: int = 0
    approved: int = 0
    rejected: int = 0
    skipped: int = 0
    # Rates
    approval_rate: float = 0.0
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    recommendation_precision: float = 0.0
    feedback_coverage: float = 0.0
    # Learning
    learning_velocity: float = 0.0
    knowledge_growth: float = 0.0
    # Source quality
    avg_source_quality: float = 0.0
    # Dataset
    dataset_size: int = 0
    signals_generated: int = 0
    artifacts_created: int = 0


@dataclass
class SourceProfile:
    """Evolving profile for a simulated source."""

    source_id: str
    quality: float
    total_articles: int = 0
    approved: int = 0
    rejected: int = 0
    keywords: dict[str, int] = field(default_factory=dict)

    @property
    def approval_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0
        return self.approved / self.total_articles

    @property
    def rejection_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0
        return self.rejected / self.total_articles


class SimulationMetrics:
    """Tracks all simulation metrics over time.

    Records snapshots at each iteration and maintains cumulative statistics.
    """

    def __init__(self) -> None:
        self._snapshots: list[MetricSnapshot] = []
        self._source_profiles: dict[str, SourceProfile] = {}
        self._category_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"approved": 0, "rejected": 0, "total": 0}
        )
        self._keyword_freq: Counter[str] = Counter()
        self._confidence_history: list[float] = []
        self._approval_rate_history: list[float] = []
        self._source_quality_history: list[float] = []
        self._dataset_growth: list[int] = []
        self._signals_count: list[int] = []
        self._decision_times: list[float] = []
        # Cumulative
        self._total_articles: int = 0
        self._total_decisions: int = 0
        self._total_approved: int = 0
        self._total_rejected: int = 0
        self._total_skipped: int = 0
        self._total_signals: int = 0
        self._total_artifacts: int = 0
        self._start_time: float = time.monotonic()

    # ── Recording ────────────────────────────────────────────────────

    def record_decision(
        self,
        source: str,
        category: str,
        topic: str,
        approved: bool,
        confidence: float,
        source_quality: float,
        keywords: list[str],
        iteration: int,
        day: int,
        timestamp: datetime,
    ) -> None:
        """Record a single simulated decision."""
        self._total_decisions += 1
        if approved:
            self._total_approved += 1
        else:
            self._total_rejected += 1

        # Source profile
        if source not in self._source_profiles:
            self._source_profiles[source] = SourceProfile(
                source_id=source, quality=source_quality,
            )
        sp = self._source_profiles[source]
        sp.total_articles += 1
        if approved:
            sp.approved += 1
        else:
            sp.rejected += 1
        # Update source quality (moving average)
        sp.quality = sp.quality * 0.95 + source_quality * 0.05

        # Keywords
        for kw in keywords:
            sp.keywords[kw] = sp.keywords.get(kw, 0) + 1
            self._keyword_freq[kw] += 1

        # Category stats
        self._category_stats[category]["total"] += 1
        if approved:
            self._category_stats[category]["approved"] += 1
        else:
            self._category_stats[category]["rejected"] += 1

        # Confidence tracking
        self._confidence_history.append(confidence)

        # Decision time
        self._decision_times.append(time.monotonic())

    def record_article(self, source: str) -> None:
        """Record that an article was ingested."""
        self._total_articles += 1
        if source in self._source_profiles:
            pass  # Already tracked via record_decision

    def record_signal(self) -> None:
        """Record a learning signal generation."""
        self._total_signals += 1

    def record_artifact(self) -> None:
        """Record a dataset artifact creation."""
        self._total_artifacts += 1

    def record_skip(self) -> None:
        """Record a skipped decision."""
        self._total_skipped += 1
        self._total_decisions += 1

    # ── Snapshot ─────────────────────────────────────────────────────

    def take_snapshot(
        self, day: int, iteration: int, timestamp: datetime,
    ) -> MetricSnapshot:
        """Take a snapshot of current metrics."""
        # Calculate rates
        approval_rate = (
            self._total_approved / self._total_decisions
            if self._total_decisions > 0
            else 0.0
        )

        # Accuracy: how often AI recommendation matched human decision
        # (simplified: approval rate when AI said APPROVE)
        accuracy = approval_rate  # Simplified for simulation

        # Average confidence
        avg_conf = (
            sum(self._confidence_history[-100:]) / min(100, len(self._confidence_history))
            if self._confidence_history
            else 0.0
        )

        # Recommendation precision: of items AI recommended APPROVE, how many approved
        recommendation_precision = approval_rate  # Simplified

        # Feedback coverage: % of articles that got a decision
        coverage = (
            self._total_decisions / self._total_articles
            if self._total_articles > 0
            else 0.0
        )

        # Learning velocity: rate of new knowledge per iteration
        learning_velocity = (
            self._total_signals / max(self._total_articles, 1)
        )

        # Knowledge growth: unique keywords + source profiles
        knowledge_growth = len(self._keyword_freq) + len(self._source_profiles)

        # Average source quality
        avg_sq = (
            sum(sp.quality for sp in self._source_profiles.values())
            / len(self._source_profiles)
            if self._source_profiles
            else 0.0
        )

        # Dataset size (simulated)
        dataset_size = self._total_articles

        snapshot = MetricSnapshot(
            timestamp=timestamp,
            day=day,
            iteration=iteration,
            total_articles=self._total_articles,
            total_decisions=self._total_decisions,
            approved=self._total_approved,
            rejected=self._total_rejected,
            skipped=self._total_skipped,
            approval_rate=approval_rate,
            accuracy=accuracy,
            avg_confidence=avg_conf,
            recommendation_precision=recommendation_precision,
            feedback_coverage=coverage,
            learning_velocity=learning_velocity,
            knowledge_growth=knowledge_growth,
            avg_source_quality=avg_sq,
            dataset_size=dataset_size,
            signals_generated=self._total_signals,
            artifacts_created=self._total_artifacts,
        )
        self._snapshots.append(snapshot)

        # Track history for charts
        self._approval_rate_history.append(approval_rate)
        self._source_quality_history.append(avg_sq)
        self._dataset_growth.append(dataset_size)
        self._signals_count.append(self._total_signals)

        return snapshot

    # ── Queries ──────────────────────────────────────────────────────

    @property
    def snapshots(self) -> list[MetricSnapshot]:
        return list(self._snapshots)

    @property
    def source_profiles(self) -> dict[str, SourceProfile]:
        return dict(self._source_profiles)

    @property
    def category_stats(self) -> dict[str, dict[str, int]]:
        return dict(self._category_stats)

    @property
    def keyword_freq(self) -> Counter[str]:
        return self._keyword_freq.copy()

    @property
    def confidence_history(self) -> list[float]:
        return list(self._confidence_history)

    @property
    def approval_rate_history(self) -> list[float]:
        return list(self._approval_rate_history)

    @property
    def source_quality_history(self) -> list[float]:
        return list(self._source_quality_history)

    @property
    def dataset_growth(self) -> list[int]:
        return list(self._dataset_growth)

    @property
    def signals_count(self) -> list[int]:
        return list(self._signals_count)

    @property
    def total_articles(self) -> int:
        return self._total_articles

    @property
    def total_decisions(self) -> int:
        return self._total_decisions

    @property
    def total_approved(self) -> int:
        return self._total_approved

    @property
    def total_rejected(self) -> int:
        return self._total_rejected

    @property
    def total_skipped(self) -> int:
        return self._total_skipped

    @property
    def total_signals(self) -> int:
        return self._total_signals

    @property
    def total_artifacts(self) -> int:
        return self._total_artifacts

    @property
    def top_sources(self) -> list[dict[str, Any]]:
        """Sources sorted by approval rate."""
        profiles = sorted(
            self._source_profiles.values(),
            key=lambda sp: sp.approval_rate,
            reverse=True,
        )
        return [
            {
                "source": sp.source_id,
                "approval_rate": sp.approval_rate,
                "total": sp.total_articles,
                "approved": sp.approved,
                "quality": sp.quality,
            }
            for sp in profiles
        ]

    @property
    def worst_sources(self) -> list[dict[str, Any]]:
        """Sources sorted by lowest approval rate."""
        return list(reversed(self.top_sources))

    @property
    def top_keywords(self) -> list[tuple[str, int]]:
        """Most frequent keywords."""
        return self._keyword_freq.most_common(15)

    @property
    def category_breakdown(self) -> list[dict[str, Any]]:
        """Category stats sorted by approval rate."""
        results = []
        for cat, stats in self._category_stats.items():
            rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0.0
            results.append({
                "category": cat,
                "approval_rate": rate,
                "total": stats["total"],
                "approved": stats["approved"],
                "rejected": stats["rejected"],
            })
        results.sort(key=lambda x: x["approval_rate"], reverse=True)
        return results

    def elapsed_seconds(self) -> float:
        """Wall-clock seconds since metrics creation."""
        return time.monotonic() - self._start_time

    def reset(self) -> None:
        """Reset all metrics."""
        self._snapshots.clear()
        self._source_profiles.clear()
        self._category_stats.clear()
        self._keyword_freq.clear()
        self._confidence_history.clear()
        self._approval_rate_history.clear()
        self._source_quality_history.clear()
        self._dataset_growth.clear()
        self._signals_count.clear()
        self._decision_times.clear()
        self._total_articles = 0
        self._total_decisions = 0
        self._total_approved = 0
        self._total_rejected = 0
        self._total_skipped = 0
        self._total_signals = 0
        self._total_artifacts = 0
        self._start_time = time.monotonic()
