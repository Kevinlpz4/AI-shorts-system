"""
ScoringService — Casos de uso para score weight adjustments.

Orchestrate ScoreWeights adjustments on the LearningModel aggregate.
All business rules are in the domain layer (LearningModel.adjust_weights).

Dependencias inyectadas (DIP):
    - model_repo: LearningModelRepository
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.result.result import Error, Result

from learning.application.commands.score_commands import AdjustScoreWeightsCommand
from learning.application.dto.model_dto import LearningModelDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.model_mapper import LearningModelMapper
from learning.application.ports.event_publisher import EventPublisher
from learning.application.ports.unit_of_work import UnitOfWork
from learning.application.queries.model_queries import GetLearningModelQuery
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import LearningModelRepository
from learning.domain.value_objects.score_weights import ScoreWeights


class ScoringService:
    """Casos de uso para score weight adjustments.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        model_repo: LearningModelRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
    ) -> None:
        self._model_repo = model_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock

    # ── Commands ──

    def execute_adjust_score_weights(
        self, cmd: AdjustScoreWeightsCommand
    ) -> Result[LearningModelDTO]:
        """Adjust scoring weights on the learning model.

        Steps:
            1. Find current LearningModel
            2. Create new ScoreWeights from cmd
            3. Call model.adjust_weights(new_weights, cmd.reason)
            4. Save model
            5. Commit
            6. Publish ScoreAdjusted event
            7. Return LearningModelDTO
        """
        with self._uow:
            try:
                # 1. Find current LearningModel
                model_result = self._model_repo.find_current()
                if model_result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(model_result.error)
                    )
                model = model_result.value

                # 2. Create new ScoreWeights from command
                new_weights = ScoreWeights(
                    relevance=cmd.weights.get("relevance", 0.0),
                    popularity=cmd.weights.get("popularity", 0.0),
                    recency=cmd.weights.get("recency", 0.0),
                    source_reliability=cmd.weights.get("source_reliability", 0.0),
                )

                # 3. Call domain method (business rules enforced here)
                model.adjust_weights(new_weights=new_weights, reason=cmd.reason)

                # 4. Save model
                self._model_repo.save(model)

                # 5. Commit
                self._uow.commit()

                # 6. Publish events (after commit)
                events = model.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                # 7. Return DTO
                return Result.success(LearningModelMapper.to_dto(model))

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

    def execute_get_learning_model(
        self, query: GetLearningModelQuery
    ) -> Result[LearningModelDTO]:
        """Get current learning model state.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            model_result = self._model_repo.find_current()
            if model_result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(model_result.error)
                )
            return Result.success(LearningModelMapper.to_dto(model_result.value))

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
