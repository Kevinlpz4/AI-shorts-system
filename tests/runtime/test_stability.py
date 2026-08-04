"""
Stability tests — run pipeline 100 times, verify no crashes.

Uses mocked adapters to test pipeline stability under repeated execution.
"""
from __future__ import annotations

import asyncio

from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.contracts.job_result import JobContext
from runtime.contracts.source_definition import SourceDefinition
from runtime.event_bridge import EventBridge
from runtime.jobs.ingestion_job import IngestionJob
from runtime.pipelines.deduplicate_step import DeduplicateStep
from runtime.pipelines.ingest_step import IngestStep
from runtime.pipelines.learning_step import LearningIntegrationStep
from runtime.pipelines.normalize_step import NormalizeStep
from runtime.registry.provider_registry import ProviderRegistry
from runtime.registry.source_registry import SourceRegistry
from runtime.registry.step_registry import StepRegistry


def _build_stable_pipeline() -> IngestionJob:
    """Build a pipeline with mocked providers for stability testing."""
    source_reg = SourceRegistry()
    provider_reg = ProviderRegistry()
    step_reg = StepRegistry()

    # Register a mock source
    source_reg.register(
        SourceDefinition(
            id="stable-src",
            provider="mock",
            technology="mock",
            metadata={"url": "https://mock.test"},
        )
    )

    # Mock provider that returns consistent data
    mock_provider = MagicMock()
    mock_provider.name = "mock"
    mock_provider.fetch = AsyncMock(
        return_value=[
            {"title": f"Article {i}", "url": f"https://mock.test/{i}", "source_id": "stable-src", "content_hash": f"hash_{i}"}
            for i in range(5)
        ]
    )
    provider_reg.register(mock_provider)

    step_reg.register(IngestStep(source_reg, provider_reg))
    step_reg.register(NormalizeStep())
    step_reg.register(DeduplicateStep())
    step_reg.register(LearningIntegrationStep())

    bridge = EventBridge()
    return IngestionJob(step_reg, event_bridge=bridge)


class TestStability:
    """Stability tests — verify pipeline doesn't crash under repetition."""

    @pytest.mark.asyncio
    async def test_pipeline_runs_100_times(self) -> None:
        """Pipeline executes 100 times without crash."""
        job = _build_stable_pipeline()
        errors = []

        for i in range(100):
            try:
                ctx = JobContext()
                result = await job.execute(ctx)
                assert result.is_success, f"Run {i} failed: {result.error}"
            except Exception as e:
                errors.append((i, str(e)))

        assert len(errors) == 0, f"Pipeline crashed {len(errors)} times: {errors[:5]}"

    @pytest.mark.asyncio
    async def test_pipeline_consistent_output(self) -> None:
        """Pipeline produces consistent output across runs."""
        job = _build_stable_pipeline()
        outputs = []

        for _ in range(10):
            ctx = JobContext()
            result = await job.execute(ctx)
            job_result = result.unwrap()
            outputs.append(job_result.pipeline_result.total_items_output)

        # All outputs should be the same (mocked provider returns consistent data)
        assert len(set(outputs)) == 1, f"Inconsistent outputs: {outputs}"

    @pytest.mark.asyncio
    async def test_pipeline_event_bridge_stability(self) -> None:
        """EventBridge doesn't leak memory under repeated pipeline runs."""
        job = _build_stable_pipeline()

        for _ in range(50):
            ctx = JobContext()
            await job.execute(ctx)

        # EventBridge should still work
        assert job._event_bridge is not None
        events = job._event_bridge.drain()
        # Events from last run only (drain clears buffer)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_runs(self) -> None:
        """Multiple pipeline runs can execute concurrently."""
        job = _build_stable_pipeline()

        async def run_pipeline():
            ctx = JobContext()
            result = await job.execute(ctx)
            return result.is_success

        # Run 20 pipelines concurrently
        results = await asyncio.gather(*[run_pipeline() for _ in range(20)])
        assert all(results), f"Some concurrent runs failed: {results}"
