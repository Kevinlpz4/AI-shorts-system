"""
Dataset Pipeline — orchestrates Feedback Accumulation → Dataset Generation → New Event.

Flow: Trigger → GenerateDatasetCommand → DatasetService → DatasetReady

When sufficient feedback is available, this pipeline:
    1. Creates a GenerateDatasetCommand from the provided parameters
    2. Executes via DatasetService.execute_generate_dataset()
    3. Emits a DatasetReady outbound integration event
    4. NO model training — only data preparation

Design note:
    This pipeline is NOT event-driven (no IntegrationEvent input). It is
    called programmatically when feedback accumulation reaches a threshold
    or on a schedule. The DatasetService handles the actual data extraction
    and export logic.
"""
from __future__ import annotations

import logging
from typing import Callable

from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.services.dataset_service import DatasetService
from learning.integration.events.learning_outbound_events import DatasetReady
from learning.integration.observability.event_context import EventContext

logger = logging.getLogger(__name__)


class DatasetPipeline:
    """Pipeline: Feedback accumulation → Dataset generation.

    When sufficient feedback is available:
        1. Create GenerateDatasetCommand
        2. Execute via DatasetService
        3. Emit DatasetReady event
        4. NO model training — only data preparation
    """

    def __init__(
        self,
        dataset_service: DatasetService,
        on_dataset_ready: Callable[[DatasetReady], None] | None = None,
    ) -> None:
        self._dataset_service = dataset_service
        self._on_dataset_ready = on_dataset_ready

    def generate_dataset(
        self,
        name: str,
        time_window_start: str,
        time_window_end: str,
        max_samples: int | None = None,
        context: EventContext | None = None,
    ) -> DatasetReady | None:
        """Generate a dataset through the pipeline.

        Args:
            name: Descriptive name for the dataset.
            time_window_start: Start of time window (ISO format string).
            time_window_end: End of time window (ISO format string).
            max_samples: Optional maximum number of samples to include.
            context: Optional observability context for traceability.

        Returns:
            DatasetReady event on success, None on failure.
            Exceptions are caught and logged — never propagated.
        """
        try:
            # 1. Create GenerateDatasetCommand
            cmd = GenerateDatasetCommand(
                name=name,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                max_samples=max_samples,
            )

            # 2. Execute via DatasetService
            result = self._dataset_service.execute_generate_dataset(cmd)

            if result.is_failure:
                logger.warning(
                    "DatasetPipeline: dataset generation failed for "
                    "name=%s: %s",
                    name,
                    result.error.message if result.error else "unknown error",
                )
                return None

            dataset_dto = result.value

            # 3. Build outbound integration event
            outbound_event = DatasetReady(
                source_boundary="learning",
                dataset_id=dataset_dto.id,
                record_count=dataset_dto.sample_count,
                format="json",
            )

            # 4. Fire callback if registered
            if self._on_dataset_ready is not None:
                try:
                    self._on_dataset_ready(outbound_event)
                except Exception as cb_error:
                    logger.error(
                        "DatasetPipeline: callback failed: %s",
                        cb_error,
                    )

            return outbound_event

        except Exception as exc:
            logger.error(
                "DatasetPipeline: unexpected error for name=%s: %s",
                name,
                exc,
            )
            return None
