"""
PipelineMetrics — tracks execution metrics per provider and per run.

Provides per-provider execution tracking (duration, items fetched,
duplicates, errors) and aggregate statistics across all providers.

Usage::

    metrics = PipelineMetrics()
    m = metrics.start_run("google-news-ai")
    # ... fetch ...
    m.items_fetched = 15
    m.items_new = 12
    metrics.finish_run(m)

    stats = metrics.get_provider_stats("google-news-ai")
    agg = metrics.get_aggregate_stats()
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ProviderMetrics:
    """Metrics for a single provider execution run.

    Attributes:
        provider_id: Source/provider identifier.
        started_at: When the fetch started.
        finished_at: When the fetch completed.
        duration_seconds: Total execution duration.
        items_fetched: Total items fetched from source.
        items_new: Items that were new (not duplicates).
        items_duplicate: Items that were duplicates.
        errors: Number of errors during fetch.
        retries: Number of retry attempts.
        status: Current status (pending, running, success, failed, degraded).
    """

    provider_id: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float = 0.0
    items_fetched: int = 0
    items_new: int = 0
    items_duplicate: int = 0
    errors: int = 0
    retries: int = 0
    status: str = "pending"


class PipelineMetrics:
    """Tracks execution metrics per provider and per run.

    Maintains a list of all provider metric runs. Provides methods
    to query individual provider stats and aggregate statistics.
    """

    def __init__(self) -> None:
        self._runs: list[ProviderMetrics] = []

    def start_run(self, provider_id: str) -> ProviderMetrics:
        """Start tracking a new provider run.

        Args:
            provider_id: The provider/source identifier.

        Returns:
            ProviderMetrics instance to populate during execution.
        """
        m = ProviderMetrics(
            provider_id=provider_id,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        self._runs.append(m)
        return m

    def finish_run(self, metrics: ProviderMetrics) -> None:
        """Mark a provider run as finished.

        Args:
            metrics: The ProviderMetrics instance from start_run().
        """
        metrics.finished_at = datetime.now(timezone.utc)
        if metrics.started_at:
            metrics.duration_seconds = (
                metrics.finished_at - metrics.started_at
            ).total_seconds()
        if metrics.status == "running":
            metrics.status = "success" if metrics.errors == 0 else "failed"

    def get_provider_stats(self, provider_id: str) -> dict | None:
        """Get the latest metrics for a provider.

        Args:
            provider_id: The provider/source identifier.

        Returns:
            Dict with provider metrics, or None if not found.
        """
        provider_runs = [
            r for r in self._runs if r.provider_id == provider_id
        ]
        if not provider_runs:
            return None

        latest = provider_runs[-1]
        return self._metrics_to_dict(latest)

    def get_all_stats(self) -> list[dict]:
        """Get metrics for all runs across all providers.

        Returns:
            List of dicts with metrics for each run.
        """
        return [self._metrics_to_dict(r) for r in self._runs]

    def get_aggregate_stats(self) -> dict:
        """Get aggregate statistics across all provider runs.

        Returns:
            Dict with total counts and averages.
        """
        if not self._runs:
            return {
                "total_providers": 0,
                "total_items_fetched": 0,
                "total_items_new": 0,
                "total_items_duplicate": 0,
                "total_errors": 0,
                "total_retries": 0,
                "avg_duration_seconds": 0.0,
            }

        total_duration = sum(r.duration_seconds for r in self._runs)
        return {
            "total_providers": len(self._runs),
            "total_items_fetched": sum(r.items_fetched for r in self._runs),
            "total_items_new": sum(r.items_new for r in self._runs),
            "total_items_duplicate": sum(r.items_duplicate for r in self._runs),
            "total_errors": sum(r.errors for r in self._runs),
            "total_retries": sum(r.retries for r in self._runs),
            "avg_duration_seconds": total_duration / len(self._runs),
        }

    def _metrics_to_dict(self, m: ProviderMetrics) -> dict:
        """Convert ProviderMetrics to dict for serialization."""
        return {
            "provider_id": m.provider_id,
            "started_at": m.started_at.isoformat() if m.started_at else None,
            "finished_at": m.finished_at.isoformat() if m.finished_at else None,
            "duration_seconds": m.duration_seconds,
            "items_fetched": m.items_fetched,
            "items_new": m.items_new,
            "items_duplicate": m.items_duplicate,
            "errors": m.errors,
            "retries": m.retries,
            "status": m.status,
        }
