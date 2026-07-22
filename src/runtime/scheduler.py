"""
PipelineScheduler — APScheduler-based scheduler for Runtime jobs.

Dispatches jobs from JobRegistry at configurable intervals.
Supports both global intervals and per-source poll intervals
from SourceDefinition.

Usage::

    scheduler = PipelineScheduler(config, job_registry)
    scheduler.start()
    # ... running ...
    scheduler.stop()
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from runtime.config import RuntimeConfig
from runtime.contracts.job_result import JobContext
from runtime.registry.job_registry import JobRegistry
from runtime.registry.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """APScheduler-based scheduler. Dispatches jobs from JobRegistry.

    Reads enabled job names from RuntimeConfig, resolves intervals
    (global default or per-source), and schedules them via APScheduler.

    Args:
        config: RuntimeConfig with enabled_jobs and pipeline_interval_minutes.
        job_registry: Registry of Job instances to dispatch to.
        source_registry: Optional SourceRegistry for per-source intervals.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        job_registry: JobRegistry,
        source_registry: SourceRegistry | None = None,
    ) -> None:
        self._config = config
        self._job_registry = job_registry
        self._source_registry = source_registry
        self._scheduler = AsyncIOScheduler()
        self._running = False

    def start(self) -> None:
        """Start the scheduler with all configured jobs."""
        self._setup_jobs()
        self._scheduler.start()
        self._running = True
        logger.info(
            "PipelineScheduler started with %d jobs",
            len(self._config.enabled_jobs),
        )

    def stop(self) -> None:
        """Gracefully stop the scheduler."""
        if self._running:
            self._scheduler.shutdown(wait=True)
            self._running = False
            logger.info("PipelineScheduler stopped")

    def _setup_jobs(self) -> None:
        """Register jobs from JobRegistry with their intervals."""
        for job_name in self._config.enabled_jobs:
            job = self._job_registry.get(job_name)
            if job is None:
                logger.warning(
                    "Job '%s' in enabled_jobs but not found in registry — skipping",
                    job_name,
                )
                continue

            interval_minutes = self._resolve_interval(job_name)
            trigger = IntervalTrigger(minutes=interval_minutes)

            self._scheduler.add_job(
                self._run_job,
                trigger=trigger,
                args=[job_name],
                id=f"job_{job_name}",
                name=f"Pipeline: {job_name}",
                replace_existing=True,
            )
            logger.info(
                "Scheduled job '%s' every %d minutes",
                job_name,
                interval_minutes,
            )

    def _resolve_interval(self, job_name: str) -> int:
        """Resolve interval for a job.

        If source_registry is provided and the job_name matches a source,
        use that source's poll_interval. Otherwise, use global config interval.
        """
        if self._source_registry:
            source = self._source_registry.get(job_name)
            if source is not None:
                # poll_interval is timedelta; convert to minutes
                total_seconds = int(source.poll_interval.total_seconds())
                minutes = max(1, total_seconds // 60)
                return minutes

        return self._config.pipeline_interval_minutes

    async def _run_job(self, job_name: str) -> None:
        """Execute a single job."""
        job = self._job_registry.get(job_name)
        if job is None:
            return

        ctx = JobContext(
            correlation_id=uuid4(),
            triggered_at=datetime.now(timezone.utc),
        )

        try:
            result = await job.execute(ctx)
            if result.is_success:
                job_result = result.unwrap()
                logger.info(
                    "Job '%s' completed: success=%s, duration=%.2fs",
                    job_name,
                    job_result.success,
                    job_result.duration_seconds,
                )
            else:
                logger.warning(
                    "Job '%s' returned failure: %s",
                    job_name,
                    result.error,
                )
        except Exception as exc:
            logger.error("Job '%s' raised exception: %s", job_name, exc)

    @property
    def is_running(self) -> bool:
        """Whether the scheduler is currently running."""
        return self._running
