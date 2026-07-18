"""
Recommendation Pipeline — orchestrates Event → Prediction → Recommendation → New Event.

Flow: RawArticleCollected → RecommendationService.recommend() → RecommendationGenerated

When a RawArticleCollected event arrives, this pipeline:
    1. Extracts source_name from the event
    2. Calls RecommendationService.recommend() (which internally
       orchestrates prediction + explanation)
    3. Emits a RecommendationGenerated outbound integration event
    4. NEVER modifies the original article — read-only pipeline

Design note:
    RecommendationService.recommend() already calls PredictionService
    internally. The pipeline does NOT make a redundant prediction call.
    The prediction_service parameter is available for future use (e.g.,
    standalone prediction without full recommendation).
"""
from __future__ import annotations

import json
import logging
from typing import Callable

from foundation.events.integration_event import IntegrationEvent

from learning.application.queries.prediction_queries import PredictApprovalQuery
from learning.application.services.prediction_service import PredictionService
from learning.application.services.recommendation_service import RecommendationService
from learning.integration.events.ingestion_events import RawArticleCollected
from learning.integration.events.learning_outbound_events import (
    RecommendationGenerated,
)
from learning.integration.observability.event_context import EventContext

logger = logging.getLogger(__name__)


class RecommendationPipeline:
    """Pipeline: New article → Prediction → Recommendation.

    When a RawArticleCollected event arrives:
        1. Extract source_name and features from event
        2. Run RecommendationService.recommend()
           (which internally uses PredictionService)
        3. Emit RecommendationGenerated event
        4. NEVER modify the original article
    """

    def __init__(
        self,
        prediction_service: PredictionService,
        recommendation_service: RecommendationService,
        on_recommendation: Callable[[IntegrationEvent], None] | None = None,
    ) -> None:
        self._prediction_service = prediction_service
        self._recommendation_service = recommendation_service
        self._on_recommendation = on_recommendation

    def handle(
        self,
        event: RawArticleCollected,
        context: EventContext | None = None,
    ) -> RecommendationGenerated | None:
        """Handle incoming article event and generate recommendation.

        Args:
            event: The RawArticleCollected integration event.
            context: Optional observability context for traceability.

        Returns:
            RecommendationGenerated event on success, None on failure.
            Exceptions are caught and logged — never propagated.
        """
        try:
            # 1. Extract data from event
            source_name = event.source_name
            article_id = event.article_id

            if not source_name:
                logger.warning(
                    "RecommendationPipeline: empty source_name in event %s",
                    event.event_id,
                )
                return None

            # 2. Build child context for traceability
            child_context: EventContext | None = None
            if context is not None:
                child_context = context.new_correlated(
                    event_type="RecommendationGenerated",
                    aggregate_id=article_id,
                )

            # 3. Call RecommendationService.recommend()
            #    (internally orchestrates prediction + explanation)
            result = self._recommendation_service.recommend(
                source_name=source_name,
                features=None,  # No feature snapshot available from event
            )

            if result.is_failure:
                logger.warning(
                    "RecommendationPipeline: recommendation failed for "
                    "source=%s: %s",
                    source_name,
                    result.error.message if result.error else "unknown error",
                )
                return None

            recommendation_dto = result.value

            # 4. Build outbound integration event
            outbound_event = RecommendationGenerated(
                source_boundary="learning",
                recommendation=recommendation_dto.recommendation,
                probability=recommendation_dto.probability,
                confidence=recommendation_dto.confidence,
                source_name=source_name,
                reasoning=json.dumps(list(recommendation_dto.reasoning)),
            )

            # 5. Fire callback if registered
            if self._on_recommendation is not None:
                try:
                    self._on_recommendation(outbound_event)
                except Exception as cb_error:
                    logger.error(
                        "RecommendationPipeline: callback failed: %s",
                        cb_error,
                    )

            return outbound_event

        except Exception as exc:
            logger.error(
                "RecommendationPipeline: unexpected error for event %s: %s",
                event.event_id,
                exc,
            )
            return None
