"""
Scenario 10: Historical Dataset Metadata

Validates dataset generation with proper metadata for historical data.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.dataset_commands import GenerateDatasetCommand

from tests.learning.e2e.conftest import record_approve


class TestHistoricalDatasetMetadata:
    """Verify dataset metadata is correct for historical exports."""

    def test_historical_dataset_metadata(
        self, seeded_factory: LearningServiceFactory
    ):
        """Export dataset returns correct metadata."""
        for i in range(5):
            record_approve(
                seeded_factory,
                topic_id=f"hist-{i}",
                source_name="source-x",
                title=f"Article {i}",
            )

        result = seeded_factory.dataset_service.execute_generate_dataset(
            GenerateDatasetCommand(
                name="Historical test",
                time_window_start="2020-01-01T00:00:00Z",
                time_window_end="2030-12-31T23:59:59Z",
            )
        )
        assert result.is_success
        dto = result.value
        assert dto.sample_count == 5
        assert dto.name == "Historical test"
        assert len(dto.id) > 0

    def test_dataset_generation_publishes_event(
        self, seeded_factory: LearningServiceFactory
    ):
        """Dataset generation publishes a DatasetGenerated event."""
        record_approve(
            seeded_factory,
            topic_id="evt-ds",
            source_name="source-y",
            title="Event Article",
        )

        seeded_factory.dataset_service.execute_generate_dataset(
            GenerateDatasetCommand(
                name="Event dataset",
                time_window_start="2020-01-01T00:00:00Z",
                time_window_end="2030-12-31T23:59:59Z",
            )
        )

        # Check events were published (may include previous feedback events too)
        events = seeded_factory.event_publisher._events
        from learning.domain.events.learning_events import DatasetGenerated

        dataset_events = [e for e in events if isinstance(e, DatasetGenerated)]
        assert len(dataset_events) >= 1
