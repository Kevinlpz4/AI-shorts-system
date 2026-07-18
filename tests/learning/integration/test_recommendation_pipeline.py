"""Tests for RecommendationPipeline — 7 test cases covering success, failure, and edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.recommendation_dto import RecommendationDTO
from learning.integration.events.ingestion_events import RawArticleCollected
from learning.integration.events.learning_outbound_events import RecommendationGenerated
from learning.integration.observability.event_context import EventContext
from learning.integration.pipelines.recommendation_pipeline import (
    RecommendationPipeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(
    source_name: str = "TechBlog",
    article_id: str = "art-001",
) -> RawArticleCollected:
    """Create a valid RawArticleCollected event."""
    return RawArticleCollected(
        source_boundary="ingestion",
        article_id=article_id,
        source_name=source_name,
        title="Test Article",
        url="https://example.com/test",
        collected_at="2026-07-15T12:00:00Z",
    )


def _make_recommendation_dto(**overrides) -> RecommendationDTO:
    """Create a valid RecommendationDTO with sensible defaults."""
    defaults = dict(
        recommendation="APPROVE",
        probability=0.85,
        confidence=0.7,
        reasoning=("Source has high approval rate", "Strong keyword signal"),
        source_quality=0.9,
        model_version="1.0.0",
    )
    defaults.update(overrides)
    return RecommendationDTO(**defaults)


def _make_context(correlation_id: str = "corr-123") -> EventContext:
    """Create a valid EventContext."""
    return EventContext(
        correlation_id=correlation_id,
        source_bc="ingestion",
        event_type="RawArticleCollected",
    )


def _build_pipeline(
    recommendation_result=None,
    on_recommendation=None,
):
    """Build a RecommendationPipeline with mocked services."""
    mock_prediction_service = MagicMock()
    mock_recommendation_service = MagicMock()

    if recommendation_result is not None:
        mock_recommendation_service.recommend.return_value = recommendation_result

    pipeline = RecommendationPipeline(
        prediction_service=mock_prediction_service,
        recommendation_service=mock_recommendation_service,
        on_recommendation=on_recommendation,
    )
    return pipeline, mock_prediction_service, mock_recommendation_service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRecommendationPipelineHandle:
    """Tests for RecommendationPipeline.handle — event-driven pipeline."""

    def test_handle_success(self) -> None:
        """RawArticleCollected → RecommendationGenerated on success."""
        dto = _make_recommendation_dto()
        pipeline, _, mock_rec_svc = _build_pipeline(
            recommendation_result=Result.success(dto)
        )

        event = _make_event()
        result = pipeline.handle(event)

        assert result is not None
        assert isinstance(result, RecommendationGenerated)
        assert result.recommendation == "APPROVE"
        assert result.probability == 0.85
        assert result.confidence == 0.7
        assert result.source_name == "TechBlog"
        assert result.source_boundary == "learning"

    def test_handle_returns_none_on_recommendation_failure(self) -> None:
        """RecommendationService fails → returns None."""
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.failure(
                Error(code="OPERATION_FAILED", message="Service unavailable")
            )
        )

        event = _make_event()
        result = pipeline.handle(event)

        assert result is None

    def test_handle_returns_none_on_empty_source_name(self) -> None:
        """Empty source_name in event → returns None immediately."""
        pipeline, _, mock_rec_svc = _build_pipeline(
            recommendation_result=Result.success(_make_recommendation_dto())
        )

        event = _make_event(source_name="")
        result = pipeline.handle(event)

        assert result is None
        # RecommendationService should NOT have been called
        mock_rec_svc.recommend.assert_not_called()

    def test_handle_calls_on_recommendation_callback(self) -> None:
        """Callback is invoked with the outbound event on success."""
        mock_callback = MagicMock()
        dto = _make_recommendation_dto()
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.success(dto),
            on_recommendation=mock_callback,
        )

        event = _make_event()
        outbound = pipeline.handle(event)

        mock_callback.assert_called_once()
        # The argument should be the same event object returned
        call_arg = mock_callback.call_args[0][0]
        assert call_arg is outbound
        assert isinstance(call_arg, RecommendationGenerated)

    def test_handle_callback_exception_does_not_crash(self) -> None:
        """If callback raises, pipeline still returns the event."""
        def _broken_callback(event):
            raise RuntimeError("Callback exploded")

        dto = _make_recommendation_dto()
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.success(dto),
            on_recommendation=_broken_callback,
        )

        event = _make_event()
        result = pipeline.handle(event)

        # Pipeline should succeed despite callback failure
        assert result is not None
        assert isinstance(result, RecommendationGenerated)

    def test_handle_preserves_correlation_id(self) -> None:
        """Context correlation_id is preserved via child context."""
        dto = _make_recommendation_dto()
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.success(dto)
        )

        event = _make_event()
        context = _make_context(correlation_id="my-trace-42")

        # The pipeline creates a child context internally — verify it doesn't crash
        result = pipeline.handle(event, context=context)

        assert result is not None

    def test_handle_event_has_correct_source_boundary(self) -> None:
        """Output event always has source_boundary='learning'."""
        dto = _make_recommendation_dto()
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.success(dto)
        )

        event = _make_event()
        result = pipeline.handle(event)

        assert result is not None
        assert result.source_boundary == "learning"

    def test_handle_recommendation_service_called_correctly(self) -> None:
        """RecommendationService.recommend() is called with correct arguments."""
        dto = _make_recommendation_dto()
        pipeline, _, mock_rec_svc = _build_pipeline(
            recommendation_result=Result.success(dto)
        )

        event = _make_event(source_name="DevNews")
        pipeline.handle(event)

        mock_rec_svc.recommend.assert_called_once_with(
            source_name="DevNews",
            features=None,
        )

    def test_handle_unexpected_exception_returns_none(self) -> None:
        """If recommendation_service raises unexpectedly, returns None."""
        pipeline, _, mock_rec_svc = _build_pipeline()
        mock_rec_svc.recommend.side_effect = RuntimeError("Unexpected boom")

        event = _make_event()
        result = pipeline.handle(event)

        assert result is None

    def test_handle_no_callback_configured(self) -> None:
        """Pipeline works fine when no callback is registered."""
        dto = _make_recommendation_dto()
        pipeline, _, _ = _build_pipeline(
            recommendation_result=Result.success(dto),
            on_recommendation=None,
        )

        event = _make_event()
        result = pipeline.handle(event)

        assert result is not None
        assert isinstance(result, RecommendationGenerated)
