"""
DatasetService — Casos de uso para generación de datasets de entrenamiento.

Orquesta la generación de datasets de entrenamiento a partir de FeedbackRecords
dentro de una ventana de tiempo específica.

Dependencias inyectadas (DIP):
    - feedback_repo: FeedbackRepository
    - source_quality_repo: SourceQualityRepository
    - dataset_exporter: DatasetExporter
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.result.result import Error, Result

from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.common.query_result import QueryResult
from learning.application.dto.dataset_dto import DatasetDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.dataset_mapper import DatasetMapper
from learning.application.ports.dataset_exporter import DatasetExporter
from learning.application.ports.event_publisher import EventPublisher
from learning.application.ports.unit_of_work import UnitOfWork
from learning.application.queries.dataset_queries import ListDatasetsQuery
from learning.domain.events.learning_events import DatasetGenerated
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    FeedbackRepository,
    SourceQualityRepository,
)


class DatasetService:
    """Casos de uso para generación de datasets de entrenamiento.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        source_quality_repo: SourceQualityRepository,
        dataset_exporter: DatasetExporter,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
    ) -> None:
        self._feedback_repo = feedback_repo
        self._source_quality_repo = source_quality_repo
        self._dataset_exporter = dataset_exporter
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock

    # ── Commands ──

    def execute_generate_dataset(
        self, cmd: GenerateDatasetCommand
    ) -> Result[DatasetDTO]:
        """Generate a training dataset from feedback within time window.

        Steps:
            1. Find feedback records in time window
            2. Map to feature vectors (samples)
            3. Export via DatasetExporter
            4. Create DatasetDTO with metadata
            5. Publish DatasetGenerated event
            6. Return DatasetDTO
        """
        with self._uow:
            try:
                # 1. Parse time window from ISO strings
                start = datetime.fromisoformat(cmd.time_window_start)
                end = datetime.fromisoformat(cmd.time_window_end)
                now = self._clock.now()

                # 2. Find feedback records in time window
                records = self._feedback_repo.find_all_in_window(start, end)

                # Apply max_samples limit
                if cmd.max_samples and len(records) > cmd.max_samples:
                    records = records[: cmd.max_samples]

                # 3. Map to feature vectors (samples)
                samples: list[dict] = []
                for record in records:
                    sample = {
                        "feedback_id": str(record.id),
                        "decision": record.decision.value,
                        "source_name": record.source_name,
                        "topic_id": record.topic_id,
                        "base_score": record.feature_snapshot.base_score,
                        "freshness_score": record.feature_snapshot.freshness_score,
                        "keyword_bonus": record.feature_snapshot.keyword_bonus,
                        "source_bonus": record.feature_snapshot.source_bonus,
                        "topic_penalty": record.feature_snapshot.topic_penalty,
                        "confidence": record.feature_snapshot.confidence,
                        "final_score": record.feature_snapshot.final_score,
                        "label": 1 if record.decision.is_approval else 0,
                    }
                    samples.append(sample)

                # 4. Export via DatasetExporter
                dataset_id = str(uuid4())
                metadata = {
                    "dataset_id": dataset_id,
                    "name": cmd.name,
                    "time_window_start": cmd.time_window_start,
                    "time_window_end": cmd.time_window_end,
                    "sample_count": len(samples),
                    "generated_at": now.isoformat(),
                }
                self._dataset_exporter.export(samples=samples, metadata=metadata)

                # 5. Publish DatasetGenerated event
                event = DatasetGenerated(
                    dataset_id=dataset_id,
                    version="1.0",
                    record_count=len(samples),
                    format="json",
                    generated_at=now,
                )
                self._event_publisher.publish(event)

                # 6. Build and return DatasetDTO
                dataset_dto = DatasetDTO(
                    id=dataset_id,
                    name=cmd.name,
                    time_window_start=cmd.time_window_start,
                    time_window_end=cmd.time_window_end,
                    sample_count=len(samples),
                    created_at=now.isoformat(),
                )
                return Result.success(dataset_dto)

            except LearningDomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    # ── Queries (solo lectura, sin UoW) ──

    def execute_list_datasets(
        self, query: ListDatasetsQuery
    ) -> Result[QueryResult[DatasetDTO]]:
        """List generated datasets.

        Solo lectura. Sin UnitOfWork.

        NOTE: No persistent dataset store exists yet.
        Returns empty list until dataset persistence is implemented.
        """
        try:
            # No persistent dataset store — return empty
            return Result.success(
                QueryResult(
                    data=[],
                    total=0,
                    page=query.page,
                    size=query.size,
                )
            )

        except LearningDomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )
