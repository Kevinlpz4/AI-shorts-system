"""
Tests for PipelineOrchestrator — executes steps from StepRegistry.

Covers:
- Executes steps in order
- Stops on fatal step failure
- Non-fatal steps continue after failure
- Emits events via EventBridge
- Empty pipeline handling
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from foundation.result.result import Error, ErrorCode, Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import PipelineResult, StepResult
from runtime.event_bridge import EventBridge
from runtime.pipelines.orchestrator import PipelineOrchestrator
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


def _make_failing_step(
    name: str,
    order: int,
    is_fatal: bool = False,
) -> MagicMock:
    """Create a mock PipelineStep that returns Result.failure."""
    step = MagicMock()
    step.name = name
    step.order = order
    step.is_fatal = is_fatal
    step.execute = AsyncMock(
        return_value=Result.failure(
            Error(code=ErrorCode.UNKNOWN, message=f"Step {name} failed")
        )
    )
    return step


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    @pytest.mark.asyncio
    async def test_executes_steps_in_order(self) -> None:
        """Orchestrator executes steps in registration order."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1, items_output=10)
        step2 = _make_step("normalize", 2, items_output=8)
        step3 = _make_step("deduplicate", 3, items_output=7)
        registry.register(step3)
        registry.register(step1)
        registry.register(step2)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)

        assert result.is_success
        pipeline_result = result.unwrap()
        assert isinstance(pipeline_result, PipelineResult)
        assert len(pipeline_result.steps) == 3
        assert pipeline_result.steps[0].step_name == "ingest"
        assert pipeline_result.steps[1].step_name == "normalize"
        assert pipeline_result.steps[2].step_name == "deduplicate"

    @pytest.mark.asyncio
    async def test_empty_pipeline(self) -> None:
        """Orchestrator handles empty step registry."""
        registry = StepRegistry()
        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)

        assert result.is_success
        pipeline_result = result.unwrap()
        assert pipeline_result.total_items_processed == 0
        assert pipeline_result.total_items_output == 0

    @pytest.mark.asyncio
    async def test_non_fatal_failure_continues(self) -> None:
        """Non-fatal step failure doesn't stop pipeline."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1, items_output=5)
        step2 = _make_failing_step("normalize", 2, is_fatal=False)
        step3 = _make_step("deduplicate", 3, items_output=3)
        registry.register(step1)
        registry.register(step2)
        registry.register(step3)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)

        assert result.is_success
        pipeline_result = result.unwrap()
        # step1 and step3 should have executed
        assert len(pipeline_result.steps) >= 2
        # Pipeline overall has errors but is still returned
        assert len(pipeline_result.errors) > 0

    @pytest.mark.asyncio
    async def test_fatal_failure_stops_pipeline(self) -> None:
        """Fatal step failure stops pipeline execution."""
        registry = StepRegistry()
        step1 = _make_failing_step("ingest", 1, is_fatal=True)
        step2 = _make_step("normalize", 2)
        step3 = _make_step("deduplicate", 3)
        registry.register(step1)
        registry.register(step2)
        registry.register(step3)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)

        pipeline_result = result.unwrap()
        # Only step1 should have executed (and failed)
        assert len(pipeline_result.steps) <= 1
        step2.execute.assert_not_awaited()
        step3.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_emits_events(self) -> None:
        """Orchestrator emits events via EventBridge."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1, items_output=10)
        registry.register(step1)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        await orchestrator.execute(ctx)

        events = bridge.drain()
        assert len(events) >= 1
        event_types = [e.event_type for e in events]
        assert "pipeline.completed" in event_types

    @pytest.mark.asyncio
    async def test_emits_failure_event(self) -> None:
        """Orchestrator emits failure event on pipeline failure."""
        registry = StepRegistry()
        step1 = _make_failing_step("ingest", 1, is_fatal=True)
        registry.register(step1)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        await orchestrator.execute(ctx)

        events = bridge.drain()
        assert len(events) >= 1
        event_types = [e.event_type for e in events]
        assert "pipeline.failed" in event_types

    @pytest.mark.asyncio
    async def test_stores_data_in_context(self) -> None:
        """Orchestrator stores step results in PipelineContext."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1)
        registry.register(step1)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        await orchestrator.execute(ctx)

        # Step should have been called with context
        step1.execute.assert_awaited_once()
        called_ctx = step1.execute.call_args[0][0]
        assert called_ctx is ctx

    @pytest.mark.asyncio
    async def test_no_event_bridge(self) -> None:
        """Orchestrator works without EventBridge."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1)
        registry.register(step1)

        orchestrator = PipelineOrchestrator(registry, event_bridge=None)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)
        assert result.is_success

    @pytest.mark.asyncio
    async def test_total_items_calculated(self) -> None:
        """PipelineResult totals are sum across all steps."""
        registry = StepRegistry()
        step1 = _make_step("ingest", 1, items_processed=20, items_output=15)
        step2 = _make_step("normalize", 2, items_processed=15, items_output=12)
        step3 = _make_step("deduplicate", 3, items_processed=12, items_output=10)
        registry.register(step1)
        registry.register(step2)
        registry.register(step3)

        bridge = EventBridge()
        orchestrator = PipelineOrchestrator(registry, bridge)
        ctx = PipelineContext()

        result = await orchestrator.execute(ctx)
        pipeline_result = result.unwrap()

        assert pipeline_result.total_items_processed == 20 + 15 + 12
        assert pipeline_result.total_items_output == 15 + 12 + 10
