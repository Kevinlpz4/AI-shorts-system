"""Tests for FeedbackPipeline — 6 test cases covering success, failure, and edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.feedback_dto import FeedbackDetailDTO
from learning.integration.events.learning_outbound_events import FeedbackRecorded
from learning.integration.observability.event_context import EventContext
from learning.integration.pipelines.feedback_pipeline import FeedbackPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feedback_dto(**overrides) -> FeedbackDetailDTO:
    """Create a valid FeedbackDetailDTO with sensible defaults."""
    defaults = dict(
        id="fb-001",
        topic_id="topic-ai",
        decision="APPROVED",
        reason=None,
        source_name="TechBlog",
        title="Why Python Is Great",
        features=None,
        created_at="2026-07-15T12:00:00Z",
    )
    defaults.update(overrides)
    return FeedbackDetailDTO(**defaults)


def _make_context(correlation_id: str = "corr-123") -> EventContext:
    """Create a valid EventContext."""
    return EventContext(
        correlation_id=correlation_id,
        source_bc="learning",
        event_type="ManualDecision",
    )


def _build_pipeline(
    decision_result=None,
    recalc_result=None,
    on_feedback_recorded=None,
):
    """Build a FeedbackPipeline with mocked services."""
    mock_decision_service = MagicMock()
    mock_signal_service = MagicMock()

    if decision_result is not None:
        mock_decision_service.execute_record_feedback.return_value = decision_result

    if recalc_result is not None:
        mock_signal_service.execute_recalculate_signals.return_value = recalc_result

    pipeline = FeedbackPipeline(
        decision_service=mock_decision_service,
        signal_service=mock_signal_service,
        on_feedback_recorded=on_feedback_recorded,
    )
    return pipeline, mock_decision_service, mock_signal_service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFeedbackPipelineHandleManualDecision:
    """Tests for FeedbackPipeline.handle_manual_decision — programmatic pipeline."""

    def test_handle_manual_decision_success(self) -> None:
        """RecordFeedbackCommand → FeedbackRecorded on success."""
        dto = _make_feedback_dto()
        pipeline, mock_dec_svc, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(3),
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Why Python Is Great",
        )

        assert result is not None
        assert isinstance(result, FeedbackRecorded)
        assert result.feedback_id == "fb-001"
        assert result.topic_id == "topic-ai"
        assert result.decision == "APPROVED"
        assert result.source_name == "TechBlog"
        assert result.source_boundary == "learning"

    def test_handle_manual_decision_with_reason(self) -> None:
        """Reason is passed through to the command."""
        dto = _make_feedback_dto(reason="High quality source")
        pipeline, mock_dec_svc, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(0),
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="REJECTED",
            source_name="TechBlog",
            title="Spam Article",
            reason="High quality source",
        )

        assert result is not None
        assert result.decision == "REJECTED"

        # Verify the command was created with the reason
        call_args = mock_dec_svc.execute_record_feedback.call_args[0][0]
        assert call_args.reason == "High quality source"
        assert call_args.decision == "REJECTED"
        assert call_args.title == "Spam Article"

    def test_handle_manual_decision_failure(self) -> None:
        """DecisionService fails → returns None."""
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.failure(
                Error(code="OPERATION_FAILED", message="Service unavailable")
            ),
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        assert result is None

    def test_handle_manual_decision_calls_on_feedback_recorded(self) -> None:
        """Callback is invoked with the outbound event on success."""
        mock_callback = MagicMock()
        dto = _make_feedback_dto()
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(0),
            on_feedback_recorded=mock_callback,
        )

        outbound = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        mock_callback.assert_called_once()
        call_arg = mock_callback.call_args[0][0]
        assert call_arg is outbound
        assert isinstance(call_arg, FeedbackRecorded)

    def test_handle_manual_decision_signal_recalc_best_effort(self) -> None:
        """Signal recalculation failure does NOT block the pipeline."""
        dto = _make_feedback_dto()
        pipeline, mock_dec_svc, mock_sig_svc = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.failure(
                Error(code="RECALC_FAILED", message="No signals found")
            ),
        )

        # Signal service raises an exception — pipeline should still succeed
        mock_sig_svc.execute_recalculate_signals.side_effect = RuntimeError(
            "Recalc exploded"
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        # Pipeline should succeed despite signal recalculation failure
        assert result is not None
        assert isinstance(result, FeedbackRecorded)

    def test_handle_manual_decision_callback_exception(self) -> None:
        """If callback raises, pipeline still returns the event."""
        def _broken_callback(event):
            raise RuntimeError("Callback exploded")

        dto = _make_feedback_dto()
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(0),
            on_feedback_recorded=_broken_callback,
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        assert result is not None
        assert isinstance(result, FeedbackRecorded)

    def test_handle_manual_decision_unexpected_exception_returns_none(self) -> None:
        """If decision_service raises unexpectedly, returns None."""
        pipeline, mock_dec_svc, _ = _build_pipeline()
        mock_dec_svc.execute_record_feedback.side_effect = RuntimeError(
            "Unexpected boom"
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        assert result is None

    def test_handle_manual_decision_signal_recalc_failure_result(self) -> None:
        """Signal recalculation returns Failure result — pipeline still succeeds."""
        dto = _make_feedback_dto()
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.failure(
                Error(code="RECALC_FAILED", message="No active signals")
            ),
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        # Pipeline succeeds even when signal recalculation fails
        assert result is not None
        assert isinstance(result, FeedbackRecorded)

    def test_handle_manual_decision_no_callback_configured(self) -> None:
        """Pipeline works fine when no callback is registered."""
        dto = _make_feedback_dto()
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(0),
            on_feedback_recorded=None,
        )

        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
        )

        assert result is not None
        assert isinstance(result, FeedbackRecorded)

    def test_handle_manual_decision_passes_context(self) -> None:
        """Context is passed through without crashing."""
        dto = _make_feedback_dto()
        pipeline, _, _ = _build_pipeline(
            decision_result=Result.success(dto),
            recalc_result=Result.success(0),
        )

        context = _make_context(correlation_id="trace-999")
        result = pipeline.handle_manual_decision(
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            title="Test",
            context=context,
        )

        assert result is not None
