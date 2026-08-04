"""
Tests for PipelineMetrics — tracks execution metrics per provider and per run.

Covers:
- Start/finish run lifecycle
- Provider stats calculation
- Aggregate stats
- Empty metrics handling
- Multiple runs for same provider
"""
from __future__ import annotations

from datetime import datetime, timezone


from runtime.monitoring.pipeline_metrics import PipelineMetrics, ProviderMetrics


class TestProviderMetrics:
    """Tests for ProviderMetrics dataclass."""

    def test_default_values(self) -> None:
        """ProviderMetrics has sensible defaults."""
        m = ProviderMetrics(
            provider_id="test",
            started_at=datetime.now(timezone.utc),
        )
        assert m.items_fetched == 0
        assert m.items_new == 0
        assert m.items_duplicate == 0
        assert m.errors == 0
        assert m.retries == 0
        assert m.status == "pending"

    def test_duration_calculation(self) -> None:
        """ProviderMetrics calculates duration correctly."""
        start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
        m = ProviderMetrics(
            provider_id="test",
            started_at=start,
            finished_at=end,
            duration_seconds=10.0,
        )
        assert m.duration_seconds == 10.0


class TestPipelineMetrics:
    """Tests for PipelineMetrics."""

    def test_start_run(self) -> None:
        """start_run creates and returns ProviderMetrics."""
        metrics = PipelineMetrics()
        m = metrics.start_run("google-news-ai")

        assert m.provider_id == "google-news-ai"
        assert m.status == "running"
        assert m.started_at is not None

    def test_finish_run(self) -> None:
        """finish_run updates ProviderMetrics with completion data."""
        metrics = PipelineMetrics()
        m = metrics.start_run("google-news-ai")
        m.items_fetched = 15
        m.items_new = 12
        m.items_duplicate = 3

        metrics.finish_run(m)

        finished = metrics.get_provider_stats("google-news-ai")
        assert finished is not None
        # finish_run auto-sets status: "success" if no errors, "failed" otherwise
        assert finished["status"] == "success"
        assert finished["items_fetched"] == 15
        assert finished["items_new"] == 12
        assert finished["items_duplicate"] == 3

    def test_get_provider_stats(self) -> None:
        """get_provider_stats returns latest run for provider."""
        metrics = PipelineMetrics()
        m1 = metrics.start_run("provider-a")
        metrics.finish_run(m1)

        stats = metrics.get_provider_stats("provider-a")
        assert stats is not None
        assert stats["provider_id"] == "provider-a"

    def test_get_provider_stats_not_found(self) -> None:
        """get_provider_stats returns None for unknown provider."""
        metrics = PipelineMetrics()
        assert metrics.get_provider_stats("nonexistent") is None

    def test_get_all_stats(self) -> None:
        """get_all_stats returns stats for all providers."""
        metrics = PipelineMetrics()
        m1 = metrics.start_run("provider-a")
        metrics.finish_run(m1)
        m2 = metrics.start_run("provider-b")
        metrics.finish_run(m2)

        all_stats = metrics.get_all_stats()
        assert len(all_stats) == 2
        provider_ids = [s["provider_id"] for s in all_stats]
        assert "provider-a" in provider_ids
        assert "provider-b" in provider_ids

    def test_get_aggregate_stats(self) -> None:
        """get_aggregate_stats computes totals across all providers."""
        metrics = PipelineMetrics()
        m1 = metrics.start_run("provider-a")
        m1.items_fetched = 10
        m1.items_new = 8
        m1.items_duplicate = 2
        m1.errors = 1
        metrics.finish_run(m1)

        m2 = metrics.start_run("provider-b")
        m2.items_fetched = 20
        m2.items_new = 18
        m2.items_duplicate = 2
        m2.errors = 0
        metrics.finish_run(m2)

        agg = metrics.get_aggregate_stats()
        assert agg["total_providers"] == 2
        assert agg["total_items_fetched"] == 30
        assert agg["total_items_new"] == 26
        assert agg["total_items_duplicate"] == 4
        assert agg["total_errors"] == 1

    def test_multiple_runs_same_provider(self) -> None:
        """Multiple runs for the same provider are tracked."""
        metrics = PipelineMetrics()

        m1 = metrics.start_run("provider-a")
        m1.items_fetched = 5
        metrics.finish_run(m1)

        m2 = metrics.start_run("provider-a")
        m2.items_fetched = 10
        metrics.finish_run(m2)

        all_stats = metrics.get_all_stats()
        assert len(all_stats) == 2  # Both runs tracked

    def test_empty_metrics(self) -> None:
        """Empty metrics returns correct defaults."""
        metrics = PipelineMetrics()

        assert metrics.get_provider_stats("any") is None
        assert metrics.get_all_stats() == []
        agg = metrics.get_aggregate_stats()
        assert agg["total_providers"] == 0
        assert agg["total_items_fetched"] == 0

    def test_status_values(self) -> None:
        """ProviderMetrics finish_run auto-sets status based on errors."""
        metrics = PipelineMetrics()

        # No errors → success
        m = metrics.start_run("test-ok")
        m.status = "running"
        metrics.finish_run(m)
        stats = metrics.get_provider_stats("test-ok")
        assert stats["status"] == "success"

        # Has errors → failed
        m2 = metrics.start_run("test-err")
        m2.errors = 1
        m2.status = "running"
        metrics.finish_run(m2)
        stats2 = metrics.get_provider_stats("test-err")
        assert stats2["status"] == "failed"

        # Custom status (not "running") is preserved
        m3 = metrics.start_run("test-degraded")
        m3.status = "degraded"
        metrics.finish_run(m3)
        stats3 = metrics.get_provider_stats("test-degraded")
        assert stats3["status"] == "degraded"
