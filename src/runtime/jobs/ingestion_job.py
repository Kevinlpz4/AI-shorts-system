"""
IngestionJob — orchestrates the full ingestion pipeline.

Chains: IngestStep → NormalizeStep → DeduplicateStep → LearningIntegrationStep
Publishes events via EventBridge on completion.

Uses PipelineOrchestrator for step execution, or falls back to
direct StepRegistry iteration.

Usage::

    job = IngestionJob(step_registry, event_bridge)
    result = await job.execute(ctx)
"""
from __future__ import annotations

import logging
import time

from foundation.result.result import Result
from runtime.contracts.job_result import JobContext, JobResult
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import PipelineResult
from runtime.event_bridge import EventBridge, RoutingEvent
from runtime.pipelines.orchestrator import PipelineOrchestrator
from runtime.registry.step_registry import StepRegistry

logger = logging.getLogger(__name__)


class IngestionJob:
    """Job that runs the ingestion pipeline.

    Uses PipelineOrchestrator to execute steps from StepRegistry.
    Publishes completion events through EventBridge.

    Args:
        step_registry: Registry containing pipeline steps.
        event_bridge: Optional EventBridge for event publishing.
    """

    name: str = "ingestion"

    def __init__(
        self,
        step_registry: StepRegistry,
        event_bridge: EventBridge | None = None,
    ) -> None:
        self._step_registry = step_registry
        self._event_bridge = event_bridge
        self._orchestrator = PipelineOrchestrator(step_registry, event_bridge)

    async def execute(self, ctx: JobContext) -> Result[JobResult]:
        """Execute the ingestion pipeline.

        Runs all registered steps via PipelineOrchestrator in sequence.
        """
        start_time = time.monotonic()
        pipeline_ctx = PipelineContext(correlation_id=ctx.correlation_id)

        # Delegate to orchestrator
        result = await self._orchestrator.execute(pipeline_ctx)

        duration = time.monotonic() - start_time

        match result:
            case Result(is_success=True) as r:
                pipeline_result = r.unwrap()
            case Result(is_success=False) as r:
                # Orchestrator failure — create a minimal PipelineResult
                pipeline_result = PipelineResult(
                    correlation_id=ctx.correlation_id,
                    success=False,
                    errors=[str(r.error)],
                )

        job_result = JobResult(
            job_name=self.name,
            success=pipeline_result.success,
            correlation_id=ctx.correlation_id,
            pipeline_result=pipeline_result,
            duration_seconds=duration,
            errors=pipeline_result.errors,
        )

        # Publish events via EventBridge
        if self._event_bridge:
            event_type = (
                "ingestion.completed" if pipeline_result.success
                else "ingestion.failed"
            )
            event = RoutingEvent(
                event_type=event_type,
                payload={
                    "correlation_id": str(ctx.correlation_id),
                    "items_processed": str(pipeline_result.total_items_processed),
                    "items_output": str(pipeline_result.total_items_output),
                    "duration_seconds": f"{duration:.2f}",
                    "errors": str(len(pipeline_result.errors)),
                },
                source="ingestion",
            )
            self._event_bridge.route(event)

        logger.info(
            "Ingestion job completed: success=%s, items=%d, duration=%.2fs",
            job_result.success,
            pipeline_result.total_items_output,
            duration,
        )

        return Result.success(job_result)
