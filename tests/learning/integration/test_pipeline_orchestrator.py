"""Tests for LearningPipelineOrchestrator — 2 test cases covering registration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from learning.integration.dispatcher.event_dispatcher import EventDispatcher
from learning.integration.events.ingestion_events import RawArticleCollected
from learning.integration.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)
from learning.integration.pipelines import LearningPipelineOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_orchestrator():
    """Build a LearningPipelineOrchestrator with mocked dependencies."""
    dispatcher = EventDispatcher()
    mock_prediction_service = MagicMock()
    mock_recommendation_service = MagicMock()

    recommendation_pipeline = RecommendationPipeline(
        prediction_service=mock_prediction_service,
        recommendation_service=mock_recommendation_service,
    )

    orchestrator = LearningPipelineOrchestrator(
        dispatcher=dispatcher,
        recommendation_pipeline=recommendation_pipeline,
    )
    return orchestrator, dispatcher, recommendation_pipeline


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLearningPipelineOrchestratorRegisterAll:
    """Tests for LearningPipelineOrchestrator.register_all — wiring."""

    def test_register_all_registers_recommendation(self) -> None:
        """After register_all, dispatcher has a handler for RawArticleCollected."""
        orchestrator, dispatcher, _ = _build_orchestrator()

        orchestrator.register_all()

        assert dispatcher.has_handlers(RawArticleCollected) is True

    def test_register_all_handler_count(self) -> None:
        """Correct number of handlers registered for RawArticleCollected."""
        orchestrator, dispatcher, _ = _build_orchestrator()

        orchestrator.register_all()

        # Currently only RawArticleCollected → RecommendationPipeline.handle
        assert dispatcher.handler_count(RawArticleCollected) == 1
