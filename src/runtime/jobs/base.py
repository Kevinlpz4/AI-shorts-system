"""
Job Protocol — contract for job implementations.

A Job encapsulates its own step selection and pipeline execution.
The scheduler dispatches to JobRegistry, NOT directly to pipelines.

Usage::

    from runtime.jobs.base import Job

    class MyJob:
        name = "my_job"

        async def execute(self, ctx: JobContext) -> Result[JobResult]:
            # ... orchestrate pipeline steps ...
            return Result.success(
                JobResult(job_name=self.name, success=True, correlation_id=ctx.correlation_id)
            )
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result
from runtime.contracts.job_result import JobContext, JobResult


class Job(Protocol):
    """Protocol for job implementations.

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
