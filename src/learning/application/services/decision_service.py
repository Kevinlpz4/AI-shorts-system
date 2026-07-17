"""
DecisionService — Casos de uso para feedback decisions.

Orquesta las operaciones de grabación y archivo de FeedbackRecord,
coordinando con SourceQualityProfile para mantener estadísticas de calidad.

Dependencias inyectadas (DIP):
    - feedback_repo: FeedbackRepository
    - source_quality_repo: SourceQualityRepository
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.result.result import Error, Result

from learning.application.commands.feedback_commands import (
    ArchiveFeedbackCommand,
    RecordFeedbackCommand,
)
from learning.application.common.query_result import QueryResult
from learning.application.dto.feedback_dto import FeedbackDetailDTO, FeedbackSummaryDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.feedback_mapper import FeedbackMapper
from learning.application.ports.event_publisher import EventPublisher
from learning.application.ports.unit_of_work import UnitOfWork
from learning.application.queries.feedback_queries import (
    GetFeedbackQuery,
    ListFeedbackQuery,
)
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import FeedbackId
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    FeedbackRepository,
    SourceQualityRepository,
)
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot


class DecisionService:
    """Casos de uso para feedback decisions.

    Coordina FeedbackRecord y SourceQualityProfile aggregate roots.
    Todas las reglas de negocio están en la capa de dominio.
    Este servicio solo coordina persistencia y publicación de eventos.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        source_quality_repo: SourceQualityRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
    ) -> None:
        self._feedback_repo = feedback_repo
        self._source_quality_repo = source_quality_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock

    # ── Commands ──

    def execute_record_feedback(
        self, cmd: RecordFeedbackCommand
    ) -> Result[FeedbackDetailDTO]:
        """Record a human feedback decision.

        Coordinates creation of FeedbackRecord and update of SourceQualityProfile.
        Business rules enforced by domain entities.

        Steps:
            1. Create FeedbackRecord (domain invariants enforced)
            2. Update SourceQualityProfile via record_decision()
            3. Save both via repos
            4. Commit UoW
            5. Publish events
            6. Return FeedbackDetailDTO
        """
        with self._uow:
            try:
                # 1. Build FeatureSnapshot from command
                features = cmd.features or {}
                snapshot = FeatureSnapshot(
                    base_score=features.get("base_score", 0.0),
                    freshness_score=features.get("freshness_score", 0.0),
                    keyword_bonus=features.get("keyword_bonus", 0.0),
                    source_bonus=features.get("source_bonus", 0.0),
                    topic_penalty=features.get("topic_penalty", 0.0),
                    confidence=features.get("confidence", 0.0),
                    final_score=features.get("final_score", 0.0),
                    timestamp=self._clock.now(),
                )

                # 2. Create FeedbackRecord (domain invariants enforced)
                decision = DecisionType(cmd.decision)
                feedback = FeedbackRecord(
                    id=FeedbackId.generate(),
                    topic_id=cmd.topic_id,
                    decision=decision,
                    reason=cmd.reason,
                    feature_snapshot=snapshot,
                    source_name=cmd.source_name,
                    title=cmd.title,
                )

                # 3. Update SourceQualityProfile if it exists
                source_result = self._source_quality_repo.find_by_source_name(
                    cmd.source_name
                )
                if source_result.is_success:
                    source_profile = source_result.value
                    # record_decision expects lowercase string: "approved", "rejected", etc.
                    source_profile.record_decision(
                        decision_type=decision.value.lower()
                    )
                    self._source_quality_repo.save(source_profile)

                # 4. Save feedback
                self._feedback_repo.save(feedback)

                # 5. Commit
                self._uow.commit()

                # 6. Publish events (after commit)
                events = feedback.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                # 7. Return DTO
                return Result.success(FeedbackMapper.to_detail(feedback))

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

    def execute_archive_feedback(
        self, cmd: ArchiveFeedbackCommand
    ) -> Result[FeedbackSummaryDTO]:
        """Archive (soft-delete) a feedback record.

        NOTE: FeedbackRecord is immutable (I-01). Archiving is implemented
        as a read-only retrieval since the domain entity cannot be modified.
        If soft-delete is needed, the domain entity must be extended first.

        Steps:
            1. Find feedback by ID
            2. Return FeedbackSummaryDTO (domain prevents modification)
        """
        try:
            feedback_id = FeedbackId.from_string(cmd.feedback_id)
            result = self._feedback_repo.find_by_id(feedback_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            # FeedbackRecord is immutable — cannot archive at domain level.
            # Return the existing record as-is.
            return Result.success(FeedbackMapper.to_summary(result.value))

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

    def execute_get_feedback(
        self, query: GetFeedbackQuery
    ) -> Result[FeedbackDetailDTO]:
        """Find feedback by ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            feedback_id = FeedbackId.from_string(query.feedback_id)
            result = self._feedback_repo.find_by_id(feedback_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(FeedbackMapper.to_detail(result.value))

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

    def execute_list_feedback(
        self, query: ListFeedbackQuery
    ) -> Result[QueryResult[FeedbackSummaryDTO]]:
        """List feedback with optional filters.

        Solo lectura. Sin UnitOfWork.

        NOTE: When no filter is provided, returns empty list.
        FeedbackRepository does not expose a generic find_all().
        """
        try:
            if query.topic_id:
                records = self._feedback_repo.find_by_topic_id(query.topic_id)
            elif query.source_name:
                records = self._feedback_repo.find_by_source(query.source_name)
            else:
                # No filter — return empty (FeedbackRepository has no find_all)
                records = []

            dtos = [FeedbackMapper.to_summary(r) for r in records]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=len(dtos),
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
