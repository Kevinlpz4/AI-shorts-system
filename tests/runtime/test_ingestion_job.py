"""
Tests for IngestionJob — full job orchestration.

Covers:
- Chains steps in correct order
- Handles missing steps
- Publishes events on completion
- Reports duration
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from foundation.result.result import Result
from runtime.contracts.job_result import JobContext
from runtime.contracts.pipeline_result import StepResult
from runtime.event_bridge import EventBridge
from runtime.jobs.ingestion_job import IngestionJob
from runtime.registry.step_registry import StepRegistry


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


class TestIngestionJob:
    """Tests for IngestionJob."""

    def test_job_name(self) -> None:
        """IngestionJob has name 'ingestion'."""
        job = IngestionJob(StepRegistry())
        assert job.name == "ingestion"

    @pytest.mark.asyncio
    async def test_executes_all_steps(self) -> None:
        """IngestionJob executes steps in order."""
        registry = StepRegistry()

        ingest = _make_step("ingest", 1, items_output=10)
        normalize = _make_step("normalize", 2, items_output=8)
        dedup = _make_step("deduplicate", 3, items_output=7)

        registry.register(ingest)
        registry.register(normalize)
        registry.register(dedup)

        job = IngestionJob(registry)
        ctx = JobContext()

        result = await job.execute(ctx)

        assert result.is_success
        job_result = result.unwrap()
        assert job_result.success is True
        assert job_result.job_name == "ingestion"

        # Verify all steps were called
        ingest.execute.assert_awaited_once()
        normalize.execute.assert_awaited_once()
        dedup.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handles_missing_step(self) -> None:
        """IngestionJob handles missing steps gracefully."""
        registry = StepRegistry()
        # Only register ingest, not normalize or dedup
        ingest = _make_step("ingest", 1)
        registry.register(ingest)

        job = IngestionJob(registry)
        ctx = JobContext()

        result = await job.execute(ctx)

        # Should still succeed with partial results
        assert result.is_success

    @pytest.mark.asyncio
    async def test_publishes_events(self) -> None:
        """IngestionJob publishes events through EventBridge."""
        registry = StepRegistry()
        ingest = _make_step("ingest", 1)
        normalize = _make_step("normalize", 2)
        dedup = _make_step("deduplicate", 3)
        registry.register(ingest)
        registry.register(normalize)
        registry.register(dedup)

        bridge = EventBridge()
        job = IngestionJob(registry, event_bridge=bridge)
        ctx = JobContext()

        result = await job.execute(ctx)

        assert result.is_success
        events = bridge.drain()
        event_types = [e.event_type for e in events]
        # Both orchestrator and job emit completion events
        assert "pipeline.completed" in event_types
        assert "ingestion.completed" in event_types

    @pytest.mark.asyncio
    async def test_publishes_failure_event(self) -> None:
        """IngestionJob publishes failure event when steps fail."""
        registry = StepRegistry()
        ingest = _make_step("ingest", 1, success=False)
        # Add errors so pipeline_result.success becomes False
        ingest.execute = AsyncMock(
            return_value=Result.success(
                StepResult(
                    step_name="ingest",
                    success=False,
                    items_processed=10,
                    items_output=0,
                    errors=["fetch failed"],
                )
            )
        )
        registry.register(ingest)

        bridge = EventBridge()
        job = IngestionJob(registry, event_bridge=bridge)
        ctx = JobContext()

        await job.execute(ctx)

        events = bridge.drain()
        event_types = [e.event_type for e in events]
        assert "ingestion.failed" in event_types

    @pytest.mark.asyncio
    async def test_records_duration(self) -> None:
        """IngestionJob records execution duration."""
        registry = StepRegistry()
        ingest = _make_step("ingest", 1)
        registry.register(ingest)

        job = IngestionJob(registry)
        ctx = JobContext()

        result = await job.execute(ctx)

        job_result = result.unwrap()
        assert job_result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_no_event_bridge(self) -> None:
        """IngestionJob works without EventBridge."""
        registry = StepRegistry()
        ingest = _make_step("ingest", 1)
        registry.register(ingest)

        job = IngestionJob(registry, event_bridge=None)
        ctx = JobContext()

        result = await job.execute(ctx)
        assert result.is_success

    @pytest.mark.asyncio
    async def test_fatal_step_stops_pipeline(self) -> None:
        """IngestionJob stops on fatal step failure."""
        registry = StepRegistry()
        ingest = _make_step("ingest", 1, success=False, is_fatal=True)
        normalize = _make_step("normalize", 2)
        dedup = _make_step("deduplicate", 3)
        registry.register(ingest)
        registry.register(normalize)
        registry.register(dedup)

        job = IngestionJob(registry)
        ctx = JobContext()

        await job.execute(ctx)

        # normalize and dedup should NOT have been called
        normalize.execute.assert_not_awaited()
        dedup.execute.assert_not_awaited()
