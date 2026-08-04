"""
Tests for PipelineScheduler — APScheduler-based job scheduling.

Covers:
- Scheduler lifecycle (start/stop)
- Job dispatch from registry
- Configurable intervals
- Graceful shutdown
- Running state tracking
- Error handling during job execution
"""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from foundation.result.result import Result
from runtime.config import RuntimeConfig
from runtime.contracts.job_result import JobContext, JobResult
from runtime.contracts.source_definition import SourceDefinition
from runtime.registry.job_registry import JobRegistry
from runtime.registry.source_registry import SourceRegistry
from runtime.scheduler import PipelineScheduler


def _make_job(
    name: str = "test_job",
    success: bool = True,
) -> MagicMock:
    """Create a mock Job."""
    job = MagicMock()
    job.name = name
    job.execute = AsyncMock(
        return_value=Result.success(
            JobResult(
                job_name=name,
                success=success,
                correlation_id=JobContext().correlation_id,
            )
        )
    )
    return job


class TestPipelineScheduler:
    """Tests for PipelineScheduler."""

    def test_initial_state(self) -> None:
        """Scheduler starts in stopped state."""
        config = RuntimeConfig(enabled_jobs=[])
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_start_sets_running(self) -> None:
        """Scheduler sets running to True after start."""
        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=60)
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()

        assert scheduler.is_running is True
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_sets_not_running(self) -> None:
        """Scheduler sets running to False after stop."""
        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=60)
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()
        scheduler.stop()

        assert scheduler.is_running is False

    def test_stop_when_not_running(self) -> None:
        """Scheduler stop is safe when not running."""
        config = RuntimeConfig(enabled_jobs=[])
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        # Should not raise
        scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_registers_configured_jobs(self) -> None:
        """Scheduler registers jobs from enabled_jobs config."""
        job = _make_job("ingestion")
        registry = JobRegistry()
        registry.register(job)

        config = RuntimeConfig(enabled_jobs=["ingestion"], pipeline_interval_minutes=60)
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()
        jobs = scheduler._scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        assert "job_ingestion" in job_ids
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_skips_unregistered_jobs(self) -> None:
        """Scheduler skips jobs not in registry."""
        registry = JobRegistry()
        config = RuntimeConfig(enabled_jobs=["nonexistent"], pipeline_interval_minutes=60)
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_multiple_jobs(self) -> None:
        """Scheduler registers multiple jobs."""
        job1 = _make_job("ingestion")
        job2 = _make_job("learning")
        registry = JobRegistry()
        registry.register(job1)
        registry.register(job2)

        config = RuntimeConfig(
            enabled_jobs=["ingestion", "learning"],
            pipeline_interval_minutes=30,
        )
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()
        jobs = scheduler._scheduler.get_jobs()
        job_ids = [j.id for j in jobs]
        assert "job_ingestion" in job_ids
        assert "job_learning" in job_ids
        assert len(jobs) == 2
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_run_job_executes(self) -> None:
        """_run_job executes the job from registry."""
        job = _make_job("test_job")
        registry = JobRegistry()
        registry.register(job)

        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=60)
        scheduler = PipelineScheduler(config, registry)

        await scheduler._run_job("test_job")

        job.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_job_missing(self) -> None:
        """_run_job is a no-op for missing job."""
        registry = JobRegistry()
        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=60)
        scheduler = PipelineScheduler(config, registry)

        await scheduler._run_job("nonexistent")

    @pytest.mark.asyncio
    async def test_run_job_exception(self) -> None:
        """_run_job handles exceptions from job execution."""
        job = MagicMock()
        job.name = "failing_job"
        job.execute = AsyncMock(side_effect=RuntimeError("Job failed"))
        registry = JobRegistry()
        registry.register(job)

        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=60)
        scheduler = PipelineScheduler(config, registry)

        await scheduler._run_job("failing_job")

    @pytest.mark.asyncio
    async def test_no_jobs_configured(self) -> None:
        """Scheduler handles empty enabled_jobs list."""
        config = RuntimeConfig(enabled_jobs=[])
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        scheduler.start()
        jobs = scheduler._scheduler.get_jobs()
        assert len(jobs) == 0
        scheduler.stop()

    def test_per_source_intervals(self) -> None:
        """Scheduler can resolve per-source poll intervals."""
        source_reg = SourceRegistry()
        source_reg.register(
            SourceDefinition(
                id="fast-source",
                provider="rss",
                technology="rss",
                poll_interval=timedelta(minutes=5),
                metadata={"url": "https://fast.test"},
            )
        )
        source_reg.register(
            SourceDefinition(
                id="slow-source",
                provider="rss",
                technology="rss",
                poll_interval=timedelta(minutes=60),
                metadata={"url": "https://slow.test"},
            )
        )

        config = RuntimeConfig(
            enabled_jobs=["ingestion"],
            pipeline_interval_minutes=30,
        )
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry, source_registry=source_reg)

        interval = scheduler._resolve_interval("fast-source")
        assert interval == 5
        interval = scheduler._resolve_interval("slow-source")
        assert interval == 60

    def test_resolve_interval_fallback(self) -> None:
        """_resolve_interval falls back to global config."""
        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=45)
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry)

        interval = scheduler._resolve_interval("any-source")
        assert interval == 45

    def test_resolve_interval_source_not_found(self) -> None:
        """_resolve_interval falls back when source not in registry."""
        source_reg = SourceRegistry()
        config = RuntimeConfig(enabled_jobs=[], pipeline_interval_minutes=20)
        registry = JobRegistry()
        scheduler = PipelineScheduler(config, registry, source_registry=source_reg)

        interval = scheduler._resolve_interval("missing-source")
        assert interval == 20
