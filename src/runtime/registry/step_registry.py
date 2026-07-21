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

from runtime.pipelines.base import PipelineStep


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
