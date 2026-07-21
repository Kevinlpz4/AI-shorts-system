"""
Job result and context contracts — output of job execution.

Usage::

    from runtime.contracts.job_result import JobContext, JobResult

    ctx = JobContext()
    result = JobResult(
        job_name="ingestion",
        success=True,
        correlation_id=ctx.correlation_id,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class JobContext:
    """Immutable context for job execution.

    Attributes:
        correlation_id: Unique identifier for this job run.
        triggered_at: Timestamp when the job was triggered.
        metadata: Job-specific metadata (source, trigger type, etc.).
    """

    correlation_id: UUID = field(default_factory=uuid4)
    triggered_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class JobResult:
    """Immutable result of a job execution.

    Attributes:
        job_name: Name of the job that was executed.
        success: Whether the job completed successfully.
        correlation_id: Unique identifier for this job run.
        pipeline_result: Optional pipeline result if the job ran a pipeline.
        duration_seconds: How long the job took to execute.
        errors: Error messages if the job had issues.
    """

    job_name: str
    success: bool
    correlation_id: UUID
    pipeline_result: object | None = None
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
