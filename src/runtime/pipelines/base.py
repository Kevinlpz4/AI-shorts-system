"""
PipelineStep Protocol — contract for pipeline step implementations.

A PipelineStep is a unit of work in a pipeline. Steps are ordered
by their ``order`` field and executed sequentially by the pipeline
orchestrator.

Usage::

    from runtime.pipelines.base import PipelineStep

    class MyStep:
        name = "my_step"
        order = 1
        is_fatal = False

        async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
            # ... do work ...
            return Result.success(StepResult(step_name=self.name, success=True))
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult


class PipelineStep(Protocol):
    """Protocol for pipeline step implementations.

    Attributes:
        name: Unique name for this step.
        order: Execution order (lower = earlier). Steps with the same
            order maintain registration order.
        is_fatal: If True, pipeline stops when this step fails.
    """

    name: str
    order: int
    is_fatal: bool

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        """Execute this pipeline step.

        Args:
            ctx: Mutable pipeline context for reading/writing step data.

        Returns:
            Result[StepResult] — Success with step output, or Failure with error.
        """
        ...
