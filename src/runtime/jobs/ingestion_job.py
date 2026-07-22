"""
IngestionJob — orchestrates the full ingestion pipeline.

Chains: IngestStep → NormalizeStep → DeduplicateStep
Publishes events via EventBridge on completion.

Usage::

    job = IngestionJob(step_registry, event_bridge)
    result = await job.execute(ctx)
"""
from __future__ import annotations

import logging
import time
from uuid import uuid4

from foundation.result.result import Result
from runtime.contracts.job_result import JobContext, JobResult
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import PipelineResult
from runtime.event_bridge import EventBridge, RoutingEvent
from runtime.jobs.base import Job
from runtime.registry.step_registry import StepRegistry

logger = logging.getLogger(__name__)


class IngestionJob:
    """Job that runs the ingestion pipeline.

    Selects steps from StepRegistry by name, executes them in order,
    and publishes completion events through EventBridge.
    """

    name: str = "ingestion"

    def __init__(
        self,
        step_registry: StepRegistry,
        event_bridge: EventBridge | None = None,
    ) -> None:
        self._step_registry = step_registry
        self._event_bridge = event_bridge

    async def execute(self, ctx: JobContext) -> Result[JobResult]:
        """Execute the ingestion pipeline.

        Runs ingest → normalize → deduplicate in sequence.
        Each step reads from and writes to PipelineContext.
        """
        start_time = time.monotonic()
        pipeline_ctx = PipelineContext(correlation_id=ctx.correlation_id)

        step_names = ["ingest", "normalize", "deduplicate"]
        step_results = []
        all_errors: list[str] = []

        for step_name in step_names:
            step = self._step_registry.get(step_name)
            if step is None:
                error = f"Step '{step_name}' not found in registry"
                logger.warning(error)
                all_errors.append(error)
                continue

            result = await step.execute(pipeline_ctx)
            match result:
                case Result(is_success=True) as r:
                    step_result = r.unwrap()
                    step_results.append(step_result)
                    if not step_result.success:
                        all_errors.extend(step_result.errors)
                        if step.is_fatal:
                            logger.error(
                                "Fatal step '%s' failed — aborting pipeline",
                                step_name,
                            )
                            break
                case Result(is_success=False) as r:
                    error_result = r.error
                    all_errors.append(str(error_result))
                    logger.warning("Step '%s' returned failure: %s", step_name, error_result)
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

        job_result = JobResult(
            job_name=self.name,
            success=pipeline_result.success,
            correlation_id=ctx.correlation_id,
            pipeline_result=pipeline_result,
            duration_seconds=duration,
            errors=all_errors,
        )

        # Publish events
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
                    "errors": str(len(all_errors)),
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
