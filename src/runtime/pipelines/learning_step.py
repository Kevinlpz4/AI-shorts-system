"""
LearningIntegrationStep — bridges normalized articles to Learning BC.

This is the fourth step in the ingestion pipeline. It:
1. Reads deduplicated items from PipelineContext
2. Prepares learning-ready data (adds scoring metadata)
3. Emits events via EventBridge for Learning BC consumption
4. Stores learning items in PipelineContext for downstream use

Usage::

    step = LearningIntegrationStep(event_bridge=bridge)
    result = await step.execute(ctx)
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.event_bridge import EventBridge, RoutingEvent
from runtime.pipelines.base import PipelineStep

logger = logging.getLogger(__name__)


class LearningIntegrationStep:
    """Pipeline step that bridges normalized articles to Learning BC.

    Prepares article data for Learning's PredictionService, ScoringService,
    and SignalService. Emits events through EventBridge so Learning can
    subscribe and process asynchronously.
    """

    name: str = "learning-integration"
    order: int = 4
    is_fatal: bool = False

    def __init__(self, event_bridge: EventBridge | None = None) -> None:
        self._event_bridge = event_bridge

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        """Process deduplicated items and emit learning events."""
        deduplicated: list[dict[str, str]] | None = ctx.get_step_result("deduplicate")  # type: ignore[assignment]

        if not deduplicated:
            logger.info("No deduplicated items for learning integration — skipping")
            return Result.success(
                StepResult(
                    step_name=self.name,
                    success=True,
                    items_processed=0,
                    items_output=0,
                    metadata={"message": "No deduplicated items"},
                )
            )

        learning_items: list[dict[str, str]] = []
        total_errors: list[str] = []

        for item in deduplicated:
            try:
                learning_item = self._prepare_learning_item(item)
                learning_items.append(learning_item)
            except Exception as exc:
                error_msg = f"Failed to prepare learning item: {exc}"
                logger.warning(error_msg)
                total_errors.append(error_msg)

        # Store in context for downstream
        ctx.set_step_result("learning", learning_items)

        # Emit events via EventBridge
        if self._event_bridge:
            # Individual item events
            for item in learning_items:
                event = RoutingEvent(
                    event_type="learning.item.ready",
                    payload={
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "source_id": item.get("source_id", ""),
                        "content_hash": item.get("content_hash", ""),
                    },
                    source="learning-integration",
                )
                self._event_bridge.route(event)

            # Batch event
            batch_event = RoutingEvent(
                event_type="learning.batch.ready",
                payload={
                    "items_count": str(len(learning_items)),
                    "sources": ",".join(
                        sorted(set(i.get("source_id", "") for i in learning_items))
                    ),
                },
                source="learning-integration",
            )
            self._event_bridge.route(batch_event)

        logger.info(
            "Learning integration: %d items prepared (%d errors)",
            len(learning_items),
            len(total_errors),
        )

        return Result.success(
            StepResult(
                step_name=self.name,
                success=True,
                items_processed=len(deduplicated),
                items_output=len(learning_items),
                errors=total_errors,
                metadata={
                    "learning_items": str(len(learning_items)),
                    "sources": str(len(set(i.get("source_id", "") for i in learning_items))),
                },
            )
        )

    def _prepare_learning_item(self, item: dict[str, str]) -> dict[str, str]:
        """Prepare a single item for Learning BC consumption.

        Adds learning-specific metadata while preserving source fields.
        """
        learning_item = dict(item)

        # Ensure required fields exist
        learning_item.setdefault("title", "Untitled")
        learning_item.setdefault("url", "")
        learning_item.setdefault("source_id", "")
        learning_item.setdefault("content_hash", "")

        # Add learning metadata
        learning_item["learning_ready"] = "true"
        learning_item["categories"] = ",".join(
            [cat for cat in item.get("categories", "").split(",") if cat]
        ) if item.get("categories") else ""

        return learning_item
