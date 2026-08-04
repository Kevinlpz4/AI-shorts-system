"""
PipelineOrchestrator — executes pipeline steps from StepRegistry.

The orchestrator reads steps from StepRegistry, executes them in order,
and builds a PipelineResult. Fatal step failures halt execution.

Usage::

    orchestrator = PipelineOrchestrator(step_registry, event_bridge)
    result = await orchestrator.execute(pipeline_ctx)
"""
from __future__ import annotations

import logging
import time

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import PipelineResult, StepResult
from runtime.event_bridge import EventBridge, RoutingEvent
from runtime.registry.step_registry import StepRegistry

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Executes pipeline steps from StepRegistry.

    Reads ordered steps from the registry, executes each one,
    and builds a PipelineResult. Emits events on completion.

    Args:
        step_registry: Registry containing ordered pipeline steps.
        event_bridge: Optional EventBridge for emitting events.
    """

    def __init__(
        self,
        step_registry: StepRegistry,
        event_bridge: EventBridge | None = None,
    ) -> None:
        self._step_registry = step_registry
        self._event_bridge = event_bridge

    async def execute(self, ctx: PipelineContext) -> Result[PipelineResult]:
        """Execute all pipeline steps in order.

        Args:
            ctx: Mutable pipeline context passed through all steps.

        Returns:
            Result[PipelineResult] with step results, totals, and errors.
        """
        start_time = time.monotonic()
        steps = self._step_registry.get_ordered_steps()
        step_results: list[StepResult] = []
        all_errors: list[str] = []

        for step in steps:
            try:
                result = await step.execute(ctx)
                match result:
                    case Result(is_success=True) as r:
                        step_result = r.unwrap()
                        step_results.append(step_result)
                        if not step_result.success:
                            all_errors.extend(step_result.errors)
                            if step.is_fatal:
                                logger.error(
                                    "Fatal step '%s' failed — aborting pipeline",
                                    step.name,
                                )
                                break
                    case Result(is_success=False) as r:
                        error_result = r.error
                        error_msg = str(error_result)
                        all_errors.append(error_msg)
                        logger.warning(
                            "Step '%s' returned failure: %s",
                            step.name,
                            error_result,
                        )
                        if step.is_fatal:
                            break
            except Exception as exc:
                error_msg = f"Step '{step.name}' raised exception: {exc}"
                all_errors.append(error_msg)
                logger.warning(error_msg)
                if step.is_fatal:
                    break

        duration = time.monotonic() - start_time
        pipeline_result = PipelineResult(
            correlation_id=ctx.correlation_id,
            steps=step_results,
            success=len(all_errors) == 0,
            total_items_processed=sum(s.items_processed for s in step_results),
            total_items_output=sum(s.items_output for s in step_results),
            errors=all_errors,
        )

        # Emit events via EventBridge
        if self._event_bridge:
            event_type = (
                "pipeline.completed" if pipeline_result.success
                else "pipeline.failed"
            )
            event = RoutingEvent(
                event_type=event_type,
                payload={
                    "correlation_id": str(ctx.correlation_id),
                    "steps_executed": str(len(step_results)),
                    "items_processed": str(pipeline_result.total_items_processed),
                    "items_output": str(pipeline_result.total_items_output),
                    "duration_seconds": f"{duration:.2f}",
                    "errors": str(len(all_errors)),
                },
                source="pipeline",
            )
            self._event_bridge.route(event)

        logger.info(
            "Pipeline completed: success=%s, steps=%d, items=%d, duration=%.2fs",
            pipeline_result.success,
            len(step_results),
            pipeline_result.total_items_output,
            duration,
        )

        return Result.success(pipeline_result)
