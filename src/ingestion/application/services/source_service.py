"""
SourceService — Casos de uso para NewsSource.

Orquesta las operaciones CRUD y de estado del aggregate NewsSource,
aplicando las reglas AL-01 (no desactivar con feeds activos) y
AL-02 (requiere al menos un feed activo para activar).

Dependencias inyectadas (DIP):
    - source_repo: NewsSourceRepository
    - feed_repo: FeedRepository
    - category_repo: CategoryRepository
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

from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
from ingestion.application.errors.error_mapper import ErrorMapper
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.application.mappers.source_mapper import SourceMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.source_queries import (
    FindSourceQuery,
    ListActiveSourcesQuery,
)
from ingestion.application.commands.source_commands import (
    DisableSourceCommand,
    EnableSourceCommand,
    RegisterSourceCommand,
    UpdateSourceCommand,
)
from ingestion.application.commands.source_category_commands import (
    AssignCategoryToSourceCommand,
    AssignTopicToSourceCommand,
)
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.entities.ids import CategoryId, SourceId, TopicId
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.ports.repositories import (
    CategoryRepository,
    FeedRepository,
    NewsSourceRepository,
    TopicRepository,
)
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl


class SourceService:
    """Casos de uso para NewsSource.

    Todos los métodos retornan ``Result[SourceDetailDTO]`` o
    ``Result[QueryResult[SourceSummaryDTO]]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        source_repo: NewsSourceRepository,
        feed_repo: FeedRepository,
        category_repo: CategoryRepository,
        topic_repo: TopicRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._source_repo = source_repo
        self._feed_repo = feed_repo
        self._category_repo = category_repo
        self._topic_repo = topic_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    # ── Commands ──

    def execute_register_source(
        self, cmd: RegisterSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Registra un nuevo NewsSource.

        Reglas:
            - Verifica unicidad del nombre (I-02).
        """
        with self._uow:
            try:
                # Verificar nombre único
                if self._source_repo.exists_by_name(cmd.name):
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.DUPLICATE_NEWS_SOURCE,
                            message=f"Source name '{cmd.name}' already exists",
                        )
                    )

                # Construir y persistir el aggregate
                source = NewsSource(
                    id=SourceId.generate(),
                    name=cmd.name,
                    source_type=SourceType(cmd.source_type),
                    source_url=SourceUrl(cmd.source_url),
                )
                self._source_repo.save(source)
                self._uow.commit()

                # After commit: pull events (ninguno esperado en creación)
                source.pull_events()

                return Result.success(SourceMapper.to_detail(source))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_update_source(
        self, cmd: UpdateSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Actualiza un NewsSource existente.

        Solo actualiza los campos provistos (no None).
        Verifica unicidad del nombre si cambia.
        """
        with self._uow:
            try:
                source_id = SourceId.from_string(cmd.source_id)
                result = self._source_repo.find_by_id(source_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                source = result.value

                # Si el nombre cambia, verificar unicidad
                if cmd.name is not None and cmd.name != source.name:
                    if self._source_repo.exists_by_name(cmd.name):
                        return Result.failure(
                            Error(
                                code=IngestionErrorCode.DUPLICATE_NEWS_SOURCE,
                                message=f"Source name '{cmd.name}' already exists",
                            )
                        )
                    source.name = cmd.name

                # Actualizar campos según presentes
                if cmd.source_url is not None:
                    source.change_url(SourceUrl(cmd.source_url))
                if cmd.source_type is not None:
                    source.change_source_type(SourceType(cmd.source_type))

                self._source_repo.save(source)
                self._uow.commit()

                # After commit: pull events
                source.pull_events()

                return Result.success(SourceMapper.to_detail(source))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_enable_source(
        self, cmd: EnableSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Habilita un NewsSource.

        AL-02: Requiere al menos un Feed activo.
        Emite SourceEnabled.
        """
        with self._uow:
            try:
                source_id = SourceId.from_string(cmd.source_id)

                # AL-02: debe tener al menos un feed activo
                active_feeds = self._feed_repo.count_active_by_source(source_id)
                if active_feeds == 0:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.NEWS_SOURCE_INACTIVE,
                            message="Source needs at least one active feed to be enabled",
                        )
                    )

                result = self._source_repo.find_by_id(source_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                source = result.value

                source.enable()
                self._source_repo.save(source)
                self._uow.commit()

                # After commit: publish events
                events = source.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                return Result.success(SourceMapper.to_detail(source))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_disable_source(
        self, cmd: DisableSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Deshabilita un NewsSource.

        AL-01: No deshabilitar si tiene Feeds activos.
        Emite SourceDisabled.
        """
        with self._uow:
            try:
                source_id = SourceId.from_string(cmd.source_id)

                # AL-01: no deshabilitar con feeds activos
                active_feeds = self._feed_repo.count_active_by_source(source_id)
                if active_feeds > 0:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.HAS_ACTIVE_FEEDS,
                            message="Cannot disable source with active feeds",
                        )
                    )

                result = self._source_repo.find_by_id(source_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                source = result.value

                source.disable(cmd.reason)
                self._source_repo.save(source)
                self._uow.commit()

                # After commit: publish events
                events = source.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                return Result.success(SourceMapper.to_detail(source))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_assign_category_to_source(
        self, cmd: AssignCategoryToSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Asigna una categoría existente a un NewsSource.

        Verifica que la categoría exista antes de asignar.
        """
        with self._uow:
            try:
                category_id = CategoryId.from_string(cmd.category_id)

                # Verificar que la categoría existe
                cat_result = self._category_repo.find_by_id(category_id)
                if cat_result.is_failure:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                            message=f"Category '{cmd.category_id}' not found",
                        )
                    )

                source_id = SourceId.from_string(cmd.source_id)
                result = self._source_repo.find_by_id(source_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                source = result.value

                source.assign_category(category_id)
                self._source_repo.save(source)
                self._uow.commit()

                # After commit: pull events
                source.pull_events()

                return Result.success(SourceMapper.to_detail(source))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_assign_topic_to_source(
        self, cmd: AssignTopicToSourceCommand
    ) -> Result[SourceDetailDTO]:
        """Asigna un topic existente a un NewsSource.

        Verifica que el topic exista antes de asignar.
        """
        with self._uow:
            try:
                topic_id = TopicId.from_string(cmd.topic_id)

                # Verificar que el topic existe
                topic_result = self._topic_repo.find_by_id(topic_id)
                if topic_result.is_failure:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.TOPIC_NOT_FOUND,
                            message=f"Topic '{cmd.topic_id}' not found",
                        )
                    )

                source_id = SourceId.from_string(cmd.source_id)
                result = self._source_repo.find_by_id(source_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                source = result.value

                source.assign_topic(topic_id)
                self._source_repo.save(source)
                self._uow.commit()

                # After commit: pull events
                source.pull_events()

                return Result.success(SourceMapper.to_detail(source))

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

    def execute_find_source(
        self, query: FindSourceQuery
    ) -> Result[SourceDetailDTO]:
        """Busca un NewsSource por ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            source_id = SourceId.from_string(query.source_id)
            result = self._source_repo.find_by_id(source_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(SourceMapper.to_detail(result.value))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )

    def execute_list_active_sources(
        self, query: ListActiveSourcesQuery
    ) -> Result[QueryResult[SourceSummaryDTO]]:
        """Lista todos los NewsSources activos.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            sources = self._source_repo.find_active()
            dtos = [SourceMapper.to_summary(s) for s in sources]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=len(dtos),
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
