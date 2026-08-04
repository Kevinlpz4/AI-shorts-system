"""
Tests for JobRegistry — register, get, get_all.

Covers:
- Register and get jobs
- Get all jobs
- List names
- Get missing job returns None
- Register overwrites
"""
from __future__ import annotations


from runtime.registry.job_registry import JobRegistry


class FakeJob:
    """Minimal fake job that satisfies Job protocol."""

    def __init__(self, name: str) -> None:
        self.name = name


class TestJobRegistry:
    """Tests for JobRegistry."""

    def test_empty_registry(self) -> None:
        """New registry has no jobs."""
        registry = JobRegistry()

        assert registry.get_all() == []
        assert registry.list_names() == []
        assert registry.get("missing") is None

    def test_register_and_get(self) -> None:
        """Register a job and retrieve by name."""
        registry = JobRegistry()
        job = FakeJob("ingestion")

        registry.register(job)

        assert registry.get("ingestion") is job

    def test_get_missing_returns_none(self) -> None:
        """Getting a nonexistent job returns None."""
        registry = JobRegistry()

        assert registry.get("nonexistent") is None

    def test_get_all(self) -> None:
        """get_all returns all registered jobs."""
        registry = JobRegistry()
        j1 = FakeJob("ingestion")
        j2 = FakeJob("learning")

        registry.register(j1)
        registry.register(j2)

        all_jobs = registry.get_all()
        assert len(all_jobs) == 2
        assert j1 in all_jobs
        assert j2 in all_jobs

    def test_list_names(self) -> None:
        """list_names returns all job names."""
        registry = JobRegistry()
        registry.register(FakeJob("ingestion"))
        registry.register(FakeJob("learning"))

        names = registry.list_names()
        assert set(names) == {"ingestion", "learning"}

    def test_register_overwrites(self) -> None:
        """Registering same name overwrites previous job."""
        registry = JobRegistry()
        original = FakeJob("ingestion")
        replacement = FakeJob("ingestion")

        registry.register(original)
        registry.register(replacement)

        assert registry.get("ingestion") is replacement
        assert len(registry.get_all()) == 1
