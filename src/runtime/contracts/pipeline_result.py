"""
Pipeline and step result contracts — immutable output of pipeline execution.

Usage::

    from runtime.contracts.pipeline_result import PipelineResult, StepResult

    step = StepResult(step_name="fetch", success=True, items_processed=10)
    pipeline = PipelineResult(correlation_id=uuid4(), steps=[step])
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class StepResult:
    """Immutable result of a single pipeline step execution.

    Attributes:
        step_name: Name of the step that produced this result.
        success: Whether the step completed successfully.
        items_processed: Number of items the step processed.
        items_output: Number of items the step outputted.
        errors: Error messages if the step had issues.
        metadata: Step-specific metadata (duration, counts, etc.).
    """

    step_name: str
    success: bool
    items_processed: int = 0
    items_output: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineResult:
    """Immutable result of a complete pipeline execution.

    Attributes:
        correlation_id: Unique identifier for this pipeline run.
        steps: List of step results in execution order.
        success: Whether the entire pipeline succeeded.
        total_items_processed: Sum of items processed across all steps.
        total_items_output: Sum of items outputted across all steps.
        errors: Accumulated error messages from all steps.
    """

    correlation_id: UUID
    steps: list[StepResult] = field(default_factory=list)
    success: bool = True
    total_items_processed: int = 0
    total_items_output: int = 0
    errors: list[str] = field(default_factory=list)
