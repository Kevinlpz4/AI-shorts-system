"""Tests for DatasetPipeline — 5 test cases covering success, failure, and edge cases."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.dataset_dto import DatasetDTO
from learning.integration.events.learning_outbound_events import DatasetReady
from learning.integration.observability.event_context import EventContext
from learning.integration.pipelines.dataset_pipeline import DatasetPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dataset_dto(**overrides) -> DatasetDTO:
    """Create a valid DatasetDTO with sensible defaults."""
    defaults = dict(
        id="ds-001",
        name="training-july",
        time_window_start="2026-07-01T00:00:00Z",
        time_window_end="2026-07-31T23:59:59Z",
        sample_count=150,
        created_at="2026-07-15T12:00:00Z",
    )
    defaults.update(overrides)
    return DatasetDTO(**defaults)


def _make_context(correlation_id: str = "corr-123") -> EventContext:
    """Create a valid EventContext."""
    return EventContext(
        correlation_id=correlation_id,
        source_bc="learning",
        event_type="DatasetGeneration",
    )


def _build_pipeline(
    dataset_result=None,
    on_dataset_ready=None,
):
    """Build a DatasetPipeline with mocked services."""
    mock_dataset_service = MagicMock()

    if dataset_result is not None:
        mock_dataset_service.execute_generate_dataset.return_value = dataset_result

    pipeline = DatasetPipeline(
        dataset_service=mock_dataset_service,
        on_dataset_ready=on_dataset_ready,
    )
    return pipeline, mock_dataset_service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDatasetPipelineGenerateDataset:
    """Tests for DatasetPipeline.generate_dataset — programmatic pipeline."""

    def test_generate_dataset_success(self) -> None:
        """GenerateDatasetCommand → DatasetReady on success."""
        dto = _make_dataset_dto()
        pipeline, mock_ds_svc = _build_pipeline(
            dataset_result=Result.success(dto),
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        assert result is not None
        assert isinstance(result, DatasetReady)
        assert result.dataset_id == "ds-001"
        assert result.record_count == 150
        assert result.format == "json"
        assert result.source_boundary == "learning"

    def test_generate_dataset_with_max_samples(self) -> None:
        """max_samples is passed through to the command."""
        dto = _make_dataset_dto(sample_count=50)
        pipeline, mock_ds_svc = _build_pipeline(
            dataset_result=Result.success(dto),
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
            max_samples=50,
        )

        assert result is not None
        assert result.record_count == 50

        # Verify the command was created with max_samples
        call_args = mock_ds_svc.execute_generate_dataset.call_args[0][0]
        assert call_args.max_samples == 50
        assert call_args.name == "training-july"

    def test_generate_dataset_failure(self) -> None:
        """DatasetService fails → returns None."""
        pipeline, _ = _build_pipeline(
            dataset_result=Result.failure(
                Error(code="OPERATION_FAILED", message="Export failed")
            ),
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        assert result is None

    def test_generate_dataset_calls_on_dataset_ready(self) -> None:
        """Callback is invoked with the outbound event on success."""
        mock_callback = MagicMock()
        dto = _make_dataset_dto()
        pipeline, _ = _build_pipeline(
            dataset_result=Result.success(dto),
            on_dataset_ready=mock_callback,
        )

        outbound = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        mock_callback.assert_called_once()
        call_arg = mock_callback.call_args[0][0]
        assert call_arg is outbound
        assert isinstance(call_arg, DatasetReady)

    def test_generate_dataset_callback_exception(self) -> None:
        """If callback raises, pipeline still returns the event."""
        def _broken_callback(event):
            raise RuntimeError("Callback exploded")

        dto = _make_dataset_dto()
        pipeline, _ = _build_pipeline(
            dataset_result=Result.success(dto),
            on_dataset_ready=_broken_callback,
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        assert result is not None
        assert isinstance(result, DatasetReady)

    def test_generate_dataset_unexpected_exception_returns_none(self) -> None:
        """If dataset_service raises unexpectedly, returns None."""
        pipeline, mock_ds_svc = _build_pipeline()
        mock_ds_svc.execute_generate_dataset.side_effect = RuntimeError(
            "Unexpected boom"
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        assert result is None

    def test_generate_dataset_no_callback_configured(self) -> None:
        """Pipeline works fine when no callback is registered."""
        dto = _make_dataset_dto()
        pipeline, _ = _build_pipeline(
            dataset_result=Result.success(dto),
            on_dataset_ready=None,
        )

        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
        )

        assert result is not None
        assert isinstance(result, DatasetReady)

    def test_generate_dataset_service_called_correctly(self) -> None:
        """DatasetService.execute_generate_dataset() called with correct command."""
        dto = _make_dataset_dto()
        pipeline, mock_ds_svc = _build_pipeline(
            dataset_result=Result.success(dto),
        )

        pipeline.generate_dataset(
            name="weekly-digest",
            time_window_start="2026-07-08T00:00:00Z",
            time_window_end="2026-07-15T23:59:59Z",
            max_samples=100,
        )

        call_args = mock_ds_svc.execute_generate_dataset.call_args[0][0]
        assert call_args.name == "weekly-digest"
        assert call_args.time_window_start == "2026-07-08T00:00:00Z"
        assert call_args.time_window_end == "2026-07-15T23:59:59Z"
        assert call_args.max_samples == 100

    def test_generate_dataset_passes_context(self) -> None:
        """Context is passed through without crashing."""
        dto = _make_dataset_dto()
        pipeline, _ = _build_pipeline(
            dataset_result=Result.success(dto),
        )

        context = _make_context(correlation_id="trace-888")
        result = pipeline.generate_dataset(
            name="training-july",
            time_window_start="2026-07-01T00:00:00Z",
            time_window_end="2026-07-31T23:59:59Z",
            context=context,
        )

        assert result is not None
