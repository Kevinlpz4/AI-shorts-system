"""Tests for DatasetService — 7 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.dto.dataset_dto import DatasetDTO
from learning.application.queries.dataset_queries import ListDatasetsQuery
from learning.application.services.dataset_service import DatasetService
from learning.application.common.query_result import QueryResult

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestDatasetServiceGenerateDataset:
    """Tests for DatasetService.execute_generate_dataset — command."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        dataset_exporter = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()
        clock.now.return_value = FIXED_TS

        service = DatasetService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            dataset_exporter=dataset_exporter,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return (
            service,
            feedback_repo,
            dataset_exporter,
            uow,
            event_publisher,
        )

    def _make_mock_record(self, decision_value: str = "APPROVED", label: int = 1):
        """Create a mock FeedbackRecord for dataset generation."""
        record = MagicMock()
        record.id = "00000000-0000-0000-0000-000000000001"
        record.decision.value = decision_value
        record.decision.is_approval = label == 1
        record.source_name = "TechBlog"
        record.topic_id = "topic-ai"
        record.feature_snapshot.base_score = 0.8
        record.feature_snapshot.freshness_score = 0.7
        record.feature_snapshot.keyword_bonus = 0.1
        record.feature_snapshot.source_bonus = 0.2
        record.feature_snapshot.topic_penalty = 0.0
        record.feature_snapshot.confidence = 0.9
        record.feature_snapshot.final_score = 0.85
        return record

    def test_generate_dataset_success(self) -> None:
        """Generate dataset with records → success + DatasetDTO."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        records = [self._make_mock_record(), self._make_mock_record()]
        feedback_repo.find_all_in_window.return_value = records
        dataset_exporter.export.return_value = "/data/dataset.json"

        cmd = GenerateDatasetCommand(
            name="Training Set v1",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
        )

        result = service.execute_generate_dataset(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, DatasetDTO)
        assert dto.name == "Training Set v1"
        assert dto.sample_count == 2
        assert dto.time_window_start == "2026-01-01T00:00:00+00:00"
        assert dto.time_window_end == "2026-07-15T00:00:00+00:00"

    def test_generate_dataset_publishes_event(self) -> None:
        """DatasetGenerated event must be published."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        feedback_repo.find_all_in_window.return_value = [self._make_mock_record()]

        cmd = GenerateDatasetCommand(
            name="Test",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
        )

        service.execute_generate_dataset(cmd)

        event_publisher.publish.assert_called_once()

    def test_generate_dataset_exports_data(self) -> None:
        """DatasetExporter.export must be called with samples and metadata."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        feedback_repo.find_all_in_window.return_value = [self._make_mock_record()]

        cmd = GenerateDatasetCommand(
            name="Test",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
        )

        service.execute_generate_dataset(cmd)

        dataset_exporter.export.assert_called_once()
        call_args = dataset_exporter.export.call_args
        samples = call_args[1]["samples"] if "samples" in call_args[1] else call_args[0][0]
        assert len(samples) == 1
        assert samples[0]["source_name"] == "TechBlog"

    def test_generate_dataset_uow_context_used(self) -> None:
        """UoW context manager must be entered for write operations."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        feedback_repo.find_all_in_window.return_value = []

        cmd = GenerateDatasetCommand(
            name="Test",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
        )

        service.execute_generate_dataset(cmd)

        # DatasetService uses `with self._uow:` but doesn't call commit()
        # directly — the UoW context manager handles transaction lifecycle
        uow.__enter__.assert_called_once()
        uow.__exit__.assert_called_once()

    def test_generate_dataset_max_samples(self) -> None:
        """max_samples limits the number of records processed."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        # 5 records but max_samples=2
        records = [self._make_mock_record() for _ in range(5)]
        feedback_repo.find_all_in_window.return_value = records

        cmd = GenerateDatasetCommand(
            name="Limited",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
            max_samples=2,
        )

        result = service.execute_generate_dataset(cmd)

        assert result.is_success
        assert result.value.sample_count == 2

    def test_generate_dataset_no_feedback(self) -> None:
        """No feedback records → dataset with 0 samples."""
        service, feedback_repo, dataset_exporter, uow, event_publisher = (
            self._make_service()
        )
        feedback_repo.find_all_in_window.return_value = []

        cmd = GenerateDatasetCommand(
            name="Empty",
            time_window_start="2026-01-01T00:00:00+00:00",
            time_window_end="2026-07-15T00:00:00+00:00",
        )

        result = service.execute_generate_dataset(cmd)

        assert result.is_success
        assert result.value.sample_count == 0


class TestDatasetServiceListDatasets:
    """Tests for DatasetService.execute_list_datasets — query (no UoW)."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        dataset_exporter = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        service = DatasetService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            dataset_exporter=dataset_exporter,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, uow

    def test_list_datasets_success(self) -> None:
        """List datasets → returns empty QueryResult (no persistent store yet)."""
        service, uow = self._make_service()

        query = ListDatasetsQuery()
        result = service.execute_list_datasets(query)

        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 0
        assert len(qr.data) == 0

    def test_list_datasets_no_uow(self) -> None:
        """Queries must NOT call UoW.commit()."""
        service, uow = self._make_service()

        query = ListDatasetsQuery()
        service.execute_list_datasets(query)

        uow.commit.assert_not_called()
