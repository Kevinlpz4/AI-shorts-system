"""
Tests for scheduler + job + pipeline integration.

Covers:
- Scheduler dispatches to IngestionJob which runs pipeline
- Full wired composition with scheduler
- Metrics tracking through pipeline execution
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from foundation.result.result import Result
from runtime.config import RuntimeConfig
from runtime.contracts.pipeline_result import StepResult
from runtime.event_bridge import EventBridge
from runtime.jobs.ingestion_job import IngestionJob
from runtime.monitoring.pipeline_metrics import PipelineMetrics
from runtime.registry.job_registry import JobRegistry
from runtime.registry.step_registry import StepRegistry
from runtime.scheduler import PipelineScheduler


def _make_step(
    name: str,
    order: int,
    items_processed: int = 10,
    items_output: int = 8,
    success: bool = True,
    is_fatal: bool = False,
) -> MagicMock:
    """Create a mock PipelineStep."""
    step = MagicMock()
    step.name = name
    step.order = order
    step.is_fatal = is_fatal
    step.execute = AsyncMock(
        return_value=Result.success(
            StepResult(
                step_name=name,
                success=success,
                items_processed=items_processed,
                items_output=items_output,
            )
        )
    )
    return step


class TestSchedulerIntegration:
    """Integration tests for scheduler + job + pipeline."""

    @pytest.mark.asyncio
    async def test_scheduler_dispatches_job(self) -> None:
        """Scheduler dispatches to IngestionJob which runs pipeline."""
        step_reg = StepRegistry()
        step_reg.register(_make_step("ingest", 1))
        step_reg.register(_make_step("normalize", 2))
        step_reg.register(_make_step("deduplicate", 3))

        bridge = EventBridge()
        job = IngestionJob(step_reg, event_bridge=bridge)

        job_reg = JobRegistry()
        job_reg.register(job)

        config = RuntimeConfig(
            enabled_jobs=["ingestion"],
            pipeline_interval_minutes=60,
        )
        scheduler = PipelineScheduler(config, job_reg)

        await scheduler._run_job("ingestion")

        events = bridge.drain()
        event_types = [e.event_type for e in events]
        assert "pipeline.completed" in event_types
        assert "ingestion.completed" in event_types

    @pytest.mark.asyncio
    async def test_metrics_tracking(self) -> None:
        """Metrics track provider execution through pipeline."""
        metrics = PipelineMetrics()

        m = metrics.start_run("google-news-ai")
        m.items_fetched = 15
        m.items_new = 12
        m.items_duplicate = 3
        metrics.finish_run(m)

        m2 = metrics.start_run("hackernews")
        m2.items_fetched = 30
        m2.items_new = 28
        m2.items_duplicate = 2
        metrics.finish_run(m2)

        agg = metrics.get_aggregate_stats()
        assert agg["total_providers"] == 2
        assert agg["total_items_fetched"] == 45
        assert agg["total_items_new"] == 40
        assert agg["total_items_duplicate"] == 5

    @pytest.mark.asyncio
    async def test_full_wired_composition(self) -> None:
        """Full composition wires all components correctly."""
        from runtime.composition import build_runtime

        manager, job = build_runtime()

        # Verify all registries are populated
        assert len(manager.sources.get_all()) == 16
        assert len(manager.providers.get_all()) == 3
        assert len(manager.steps.list_names()) == 4  # ingest, normalize, deduplicate, learning
        assert len(manager.jobs.list_names()) == 1

        # Verify job name
        assert job.name == "ingestion"

        # Verify step names
        step_names = manager.steps.list_names()
        assert "ingest" in step_names
        assert "normalize" in step_names
        assert "deduplicate" in step_names
        assert "learning-integration" in step_names

    @pytest.mark.asyncio
    async def test_full_runtime_composition(self) -> None:
        """Full runtime composition includes scheduler and metrics."""
        from runtime.composition import build_full_runtime

        runtime = build_full_runtime()

        assert "config" in runtime
        assert "registry_manager" in runtime
        assert "scheduler" in runtime
        assert "metrics" in runtime
        assert "ingestion_job" in runtime

        # Scheduler should be in stopped state
        assert runtime["scheduler"].is_running is False

        # Metrics should be empty
        agg = runtime["metrics"].get_aggregate_stats()
        assert agg["total_providers"] == 0

    @pytest.mark.asyncio
    async def test_scheduler_with_mock_composition(self) -> None:
        """Scheduler wires correctly with composed job registry (mocked steps)."""
        # Build a minimal composition with mock steps — no real HTTP calls
        step_reg = StepRegistry()
        step_reg.register(_make_step("ingest", 1))
        step_reg.register(_make_step("normalize", 2))
        step_reg.register(_make_step("deduplicate", 3))

        bridge = EventBridge()
        job = IngestionJob(step_reg, event_bridge=bridge)

        job_reg = JobRegistry()
        job_reg.register(job)

        config = RuntimeConfig(
            enabled_jobs=["ingestion"],
            pipeline_interval_minutes=60,
        )
        scheduler = PipelineScheduler(config, job_reg)

        # Run job through scheduler
        await scheduler._run_job("ingestion")

        # Verify pipeline executed
        events = bridge.drain()
        event_types = [e.event_type for e in events]
        assert "pipeline.completed" in event_types

    @pytest.mark.asyncio
    async def test_scheduler_start_stop_lifecycle(self) -> None:
        """Scheduler start/stop lifecycle works correctly."""
        step_reg = StepRegistry()
        step_reg.register(_make_step("ingest", 1))
        job = IngestionJob(step_reg)
        job_reg = JobRegistry()
        job_reg.register(job)

        config = RuntimeConfig(
            enabled_jobs=["ingestion"],
            pipeline_interval_minutes=60,
        )
        scheduler = PipelineScheduler(config, job_reg)

        scheduler.start()
        assert scheduler.is_running is True

        jobs = scheduler._scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "job_ingestion"

        scheduler.stop()
        assert scheduler.is_running is False
