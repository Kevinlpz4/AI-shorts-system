"""
JobRegistry — manages Job instances.

Jobs are registered by name and can be retrieved individually or in bulk.

Usage::

    from runtime.registry.job_registry import JobRegistry

    registry = JobRegistry()
    registry.register(ingestion_job)
    job = registry.get("ingestion")
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result
from runtime.contracts.job_result import JobContext, JobResult


class Job(Protocol):
    """Protocol for jobs — units of orchestrated work.

    A Job encapsulates its own step selection and pipeline execution.
    The scheduler dispatches to JobRegistry, NOT directly to pipelines.

    Attributes:
        name: Unique name for this job (e.g., ``"ingestion"``, ``"learning"``).
    """

    name: str

    async def execute(self, ctx: JobContext) -> Result[JobResult]:
        """Execute this job.

        Args:
            ctx: Job execution context with correlation_id and metadata.

        Returns:
            Result[JobResult] — Success with job output, or Failure with error.
        """
        ...


class JobRegistry:
    """Registry for Job instances.

    Backed by a dict keyed by job name. Registration is idempotent.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def register(self, job: Job) -> None:
        """Register a job. Overwrites if name already exists."""
        self._jobs[job.name] = job

    def get(self, name: str) -> Job | None:
        """Get a job by name, or None if not found."""
        return self._jobs.get(name)

    def get_all(self) -> list[Job]:
        """Return all registered jobs."""
        return list(self._jobs.values())

    def list_names(self) -> list[str]:
        """Return all registered job names."""
        return list(self._jobs.keys())
