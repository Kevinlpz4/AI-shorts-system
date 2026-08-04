"""
Tests for PipelineStep Protocol and Job Protocol (mock implementations).

Covers:
- PipelineStep protocol compliance via mock
- Job protocol compliance via mock
"""
from __future__ import annotations


import pytest

from runtime.contracts.job_result import JobContext, JobResult
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.pipelines.base import PipelineStep
from foundation.result.result import Result


class MockPipelineStep:
    """Mock that satisfies PipelineStep Protocol."""

    def __init__(
        self,
        name: str = "mock_step",
        order: int = 1,
        is_fatal: bool = False,
    ) -> None:
        self.name = name
        self.order = order
        self.is_fatal = is_fatal

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        return Result.success(
            StepResult(step_name=self.name, success=True, items_processed=1)
        )


class FailingMockStep:
    """Mock step that returns a Failure result."""

    def __init__(self) -> None:
        self.name = "failing_step"
        self.order = 10
        self.is_fatal = True

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        from foundation.result.result import Error, ErrorCode

        return Result.failure(
            Error(code=ErrorCode.UNKNOWN, message="Step execution failed")
        )


class MockJob:
    """Mock that satisfies Job Protocol."""

    def __init__(self, name: str = "mock_job") -> None:
        self.name = name

    async def execute(self, ctx: JobContext) -> Result[JobResult]:
        return Result.success(
            JobResult(
                job_name=self.name,
                success=True,
                correlation_id=ctx.correlation_id,
            )
        )


class FailingMockJob:
    """Mock job that returns a Failure result."""

    def __init__(self) -> None:
        self.name = "failing_job"

    async def execute(self, ctx: JobContext) -> Result[JobResult]:
        from foundation.result.result import Error, ErrorCode

        return Result.failure(
            Error(code=ErrorCode.UNKNOWN, message="Job execution failed")
        )


class TestPipelineStepProtocol:
    """Tests for PipelineStep Protocol compliance."""

    @pytest.mark.asyncio
    async def test_mock_step_satisfies_protocol(self) -> None:
        """MockPipelineStep satisfies PipelineStep protocol."""
        step: PipelineStep = MockPipelineStep(name="fetch", order=1)
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.step_name == "fetch"
        assert step_result.success is True
        assert step_result.items_processed == 1

    def test_step_has_name(self) -> None:
        """PipelineStep must have a name attribute."""
        step = MockPipelineStep(name="transform")
        assert step.name == "transform"

    def test_step_has_order(self) -> None:
        """PipelineStep must have an order attribute."""
        step = MockPipelineStep(order=5)
        assert step.order == 5

    def test_step_has_is_fatal(self) -> None:
        """PipelineStep must have an is_fatal attribute."""
        step = MockPipelineStep(is_fatal=True)
        assert step.is_fatal is True

    @pytest.mark.asyncio
    async def test_failing_step(self) -> None:
        """FailingMockStep returns a Failure result."""
        step: PipelineStep = FailingMockStep()
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_failure
