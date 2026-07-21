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

from runtime.jobs.base import Job


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
