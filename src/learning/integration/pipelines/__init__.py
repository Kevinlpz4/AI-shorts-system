"""
Learning Pipeline Orchestrator — registers all pipeline handlers with the EventDispatcher.

Central point for all event-driven flows in the Learning BC. Each pipeline
is registered as a handler for its specific event type. The orchestrator
does NOT contain business logic — it only wires pipelines to events.
"""
from __future__ import annotations

from learning.integration.dispatcher.event_dispatcher import EventDispatcher
from learning.integration.events.ingestion_events import RawArticleCollected
from learning.integration.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)


class LearningPipelineOrchestrator:
    """Orchestrates all Learning pipelines via the event dispatcher.

    Registers pipeline handlers with the dispatcher.
    Central point for all event-driven flows.

    Current registrations:
        - RawArticleCollected → RecommendationPipeline.handle

    Future registrations (when pipelines are implemented):
        - FeedbackPipeline
        - DatasetPipeline
    """

    def __init__(
        self,
        dispatcher: EventDispatcher,
        recommendation_pipeline: RecommendationPipeline,
    ) -> None:
        self._dispatcher = dispatcher
        self._recommendation_pipeline = recommendation_pipeline

    def register_all(self) -> None:
        """Register all pipeline handlers with the dispatcher."""
        self._dispatcher.register(
            RawArticleCollected,
            self._recommendation_pipeline.handle,
        )
