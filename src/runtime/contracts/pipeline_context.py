"""
Pipeline context — mutable state carried across pipeline steps.

Usage::

    from runtime.contracts.pipeline_context import PipelineContext

    ctx = PipelineContext()
    ctx.set_step_result("fetch", {"items": 10})
    result = ctx.get_step_result("fetch")  # {"items": 10}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class PipelineContext:
    """Mutable context passed through pipeline steps.

    Each step reads from and writes to this context, enabling data flow
    between steps without tight coupling.

    Attributes:
        correlation_id: Unique identifier for this pipeline run.
        step_data: Results stored by each step, keyed by step name.
        errors: Accumulated error messages from all steps.
    """

    correlation_id: UUID = field(default_factory=uuid4)
    step_data: dict[str, object] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def set_step_result(self, step_name: str, result: object) -> None:
        """Store a step's result for downstream steps.

        Args:
            step_name: Name of the step that produced this result.
            result: The result value (any type).
        """
        self.step_data[step_name] = result

    def get_step_result(self, step_name: str) -> object | None:
        """Retrieve a previous step's result by name.

        Args:
            step_name: Name of the step whose result to retrieve.

        Returns:
            The step's result, or None if no result exists for that name.
        """
        return self.step_data.get(step_name)
