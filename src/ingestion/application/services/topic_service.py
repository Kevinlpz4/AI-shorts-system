"""
TopicService — Casos de uso para Topic.

Orquesta las operaciones CRUD y de estado de la entity Topic,
aplicando las reglas de unicidad de nombre (I-23) y validación
de nombre no vacío (I-22).

Dependencias inyectadas (DIP):
    - topic_repo: TopicRepository
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort
    - uuid_provider: UUIDProvider

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""

from __future__ import annotations

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result

from ingestion.application.dto.topic_dto import (
    TopicDetailDTO,
    TopicSummaryDTO,
)
from ingestion.application.errors.error_mapper import ErrorMapper
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.application.mappers.topic_mapper import TopicMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.topic_queries import (
    FindTopicQuery,
    ListTopicsQuery,
)
from ingestion.application.commands.topic_commands import (
    ActivateTopicCommand,
    CreateTopicCommand,
    DeactivateTopicCommand,
    UpdateTopicCommand,
)
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.entities.ids import TopicId
from ingestion.domain.entities.topic import Topic
from ingestion.domain.ports.repositories import TopicRepository


class TopicService:
    """Casos de uso para Topic.

    Todos los métodos retornan ``Result[TopicDetailDTO]`` o
    ``Result[QueryResult[TopicSummaryDTO]]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        topic_repo: TopicRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._topic_repo = topic_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    # ── Commands ──

    def execute_create_topic(
        self, cmd: CreateTopicCommand
    ) -> Result[TopicDetailDTO]:
        """Crea un nuevo Topic.

        Reglas:
            - Verifica unicidad del nombre (I-23).
            - Nombre no vacío validado por Topic entity (I-22).
        """
        with self._uow:
            try:
                # Verificar nombre único
                if self._topic_repo.exists_by_name(cmd.name):
                    return Result.failure(
                        Error(
                            code=ApplicationErrorCode.COMMAND_INVALID,
                            message=f"Topic name '{cmd.name}' already exists",
                        )
                    )

                # Construir entity
                topic = Topic(
                    id=TopicId.generate(),
                    name=cmd.name,
                    description=cmd.description,
                )

                self._topic_repo.save(topic)
                self._uow.commit()

                return Result.success(TopicMapper.to_detail(topic))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_update_topic(
        self, cmd: UpdateTopicCommand
    ) -> Result[TopicDetailDTO]:
        """Actualiza un Topic existente.

        Solo actualiza los campos provistos (no None).
        Verifica unicidad del nombre si cambia.
        """
        with self._uow:
            try:
                topic_id = TopicId.from_string(cmd.topic_id)
                result = self._topic_repo.find_by_id(topic_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                topic = result.value

                if cmd.name is not None:
                    # Verificar unicidad si el nombre cambia
                    if (
                        cmd.name != topic.name
                        and self._topic_repo.exists_by_name(cmd.name)
                    ):
                        return Result.failure(
                            Error(
                                code=ApplicationErrorCode.COMMAND_INVALID,
                                message=f"Topic name '{cmd.name}' already exists",
                            )
                        )
                    topic.rename(cmd.name)
                if cmd.description is not None:
                    topic.update_description(cmd.description)

                self._topic_repo.save(topic)
                self._uow.commit()

                return Result.success(TopicMapper.to_detail(topic))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_activate_topic(
        self, cmd: ActivateTopicCommand
    ) -> Result[TopicDetailDTO]:
        """Activa un Topic."""
        with self._uow:
            try:
                topic_id = TopicId.from_string(cmd.topic_id)
                result = self._topic_repo.find_by_id(topic_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                topic = result.value

                topic.activate()
                self._topic_repo.save(topic)
                self._uow.commit()

                return Result.success(TopicMapper.to_detail(topic))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_deactivate_topic(
        self, cmd: DeactivateTopicCommand
    ) -> Result[TopicDetailDTO]:
        """Desactiva un Topic."""
        with self._uow:
            try:
                topic_id = TopicId.from_string(cmd.topic_id)
                result = self._topic_repo.find_by_id(topic_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                topic = result.value

                topic.deactivate()
                self._topic_repo.save(topic)
                self._uow.commit()

                return Result.success(TopicMapper.to_detail(topic))

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

    def execute_find_topic(
        self, query: FindTopicQuery
    ) -> Result[TopicDetailDTO]:
        """Busca un Topic por ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            topic_id = TopicId.from_string(query.topic_id)
            result = self._topic_repo.find_by_id(topic_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(TopicMapper.to_detail(result.value))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )

    def execute_list_topics(
        self, query: ListTopicsQuery
    ) -> Result[QueryResult[TopicSummaryDTO]]:
        """Lista todos los Topics.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            topics = self._topic_repo.find_all()
            dtos = [TopicMapper.to_summary(t) for t in topics]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=len(dtos),
                    page=query.page,
                    size=query.size,
                )
            )
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )
