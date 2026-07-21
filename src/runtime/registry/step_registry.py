"""
StepRegistry — manages PipelineStep instances.

Steps are registered by name and retrieved in order via ``get_ordered_steps()``.

Usage::

    from runtime.registry.step_registry import StepRegistry

    registry = StepRegistry()
    registry.register(ingest_step)
    registry.register(transform_step)
    ordered = registry.get_ordered_steps()  # sorted by order field
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult


class PipelineStep(Protocol):
    """Protocol for pipeline steps.

    A PipelineStep is a unit of work in a pipeline. Steps are ordered
    by the ``order`` field and executed sequentially.

    Attributes:
        name: Unique name for this step.
        order: Execution order (lower = earlier).
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


class StepRegistry:
    """Registry for PipelineStep instances.

    Backed by a dict keyed by step name. Steps are retrieved in
    sorted order by their ``order`` field.
    """

    def __init__(self) -> None:
        self._steps: dict[str, PipelineStep] = {}

    def register(self, step: PipelineStep) -> None:
        """Register a step. Overwrites if name already exists."""
        self._steps[step.name] = step

    def get(self, name: str) -> PipelineStep | None:
        """Get a step by name, or None if not found."""
        return self._steps.get(name)

    def get_ordered_steps(self) -> list[PipelineStep]:
        """Return all steps sorted by ``order`` field (ascending)."""
        return sorted(self._steps.values(), key=lambda s: s.order)

    def list_names(self) -> list[str]:
        """Return all registered step names."""
        return list(self._steps.keys())
