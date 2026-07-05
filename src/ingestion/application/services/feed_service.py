"""
FeedService — Casos de uso para Feed.

Orquesta las operaciones CRUD, estado y fetch del aggregate Feed,
aplicando las reglas AL-03 (source_id referencia existente) y
AL-04 (no crear feed bajo source inactivo).

Dependencias inyectadas (DIP):
    - feed_repo: FeedRepository
    - source_repo: NewsSourceRepository
    - category_repo: CategoryRepository
    - topic_repo: TopicRepository
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort
    - uuid_provider: UUIDProvider

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""

from __future__ import annotations

from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result

from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.application.errors.error_mapper import ErrorMapper
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.application.mappers.feed_mapper import FeedMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.feed_queries import FindFeedQuery, ListFeedsQuery
from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
    UpdateFeedCommand,
)
from ingestion.application.commands.feed_category_commands import (
    AssignCategoryToFeedCommand,
    AssignTopicToFeedCommand,
)
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import CategoryId, FeedId, SourceId, TopicId
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.ports.repositories import (
    CategoryRepository,
    FeedRepository,
    NewsSourceRepository,
    TopicRepository,
)
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


class FeedService:
    """Casos de uso para Feed.

    Todos los métodos retornan ``Result[FeedDetailDTO]`` o
    ``Result[QueryResult[FeedSummaryDTO]]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        feed_repo: FeedRepository,
        source_repo: NewsSourceRepository,
        category_repo: CategoryRepository,
        topic_repo: TopicRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._feed_repo = feed_repo
        self._source_repo = source_repo
        self._category_repo = category_repo
        self._topic_repo = topic_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    # ── Commands ──

    def execute_register_feed(
        self, cmd: RegisterFeedCommand
    ) -> Result[FeedDetailDTO]:
        """Registra un nuevo Feed bajo un NewsSource.

        Reglas:
            - AL-03: source_id debe referenciar un NewsSource existente.
            - AL-04: No crear Feed bajo un NewsSource inactivo.
            - URL única dentro del mismo source.
        """
        with self._uow:
            try:
                source_id = SourceId.from_string(cmd.source_id)

                # AL-03: source_id debe referenciar un NewsSource existente
                source_result = self._source_repo.find_by_id(source_id)
                if source_result.is_failure:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                            message=f"Source '{cmd.source_id}' not found",
                        )
                    )
                source = source_result.value

                # AL-04: No crear Feed bajo NewsSource inactivo
                if not source.is_active:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.NEWS_SOURCE_INACTIVE,
                            message="Cannot create feed under inactive source",
                        )
                    )

                # Verificar URL única dentro del source
                if self._feed_repo.exists_by_source_and_url(
                    source_id, ArticleUrl(cmd.url)
                ):
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.DUPLICATE_FEED_URL,
                            message=f"Feed URL '{cmd.url}' already exists for this source",
                        )
                    )

                # Verificar categorías (si se proveen)
                if cmd.categories:
                    for cid_str in cmd.categories:
                        cat_result = self._category_repo.find_by_id(
                            CategoryId.from_string(cid_str)
                        )
                        if cat_result.is_failure:
                            return Result.failure(
                                Error(
                                    code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                                    message=f"Category '{cid_str}' not found",
                                )
                            )

                # Verificar topics (si se proveen)
                if cmd.topics:
                    for tid_str in cmd.topics:
                        topic_result = self._topic_repo.find_by_id(
                            TopicId.from_string(tid_str)
                        )
                        if topic_result.is_failure:
                            return Result.failure(
                                Error(
                                    code=IngestionErrorCode.TOPIC_NOT_FOUND,
                                    message=f"Topic '{tid_str}' not found",
                                )
                            )

                # Construir Feed
                categories = (
                    [CategoryId.from_string(c) for c in cmd.categories]
                    if cmd.categories
                    else None
                )
                topics = (
                    [TopicId.from_string(t) for t in cmd.topics]
                    if cmd.topics
                    else None
                )

                feed = Feed(
                    id=FeedId.generate(),
                    source_id=source_id,
                    url=ArticleUrl(cmd.url),
                    label=ArticleTitle(cmd.label),
                    language=Language(cmd.language),
                    sync_policy=SyncPolicy(
                        mode=SyncMode(cmd.sync_mode),
                        interval_minutes=cmd.sync_interval_minutes,
                        max_retries=cmd.sync_max_retries,
                    ),
                    categories=categories,
                    topics=topics,
                )

                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_update_feed(
        self, cmd: UpdateFeedCommand
    ) -> Result[FeedDetailDTO]:
        """Actualiza un Feed existente.

        Solo actualiza los campos provistos (no None).
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                # Actualizar campos según presentes
                if cmd.url is not None:
                    feed.url = ArticleUrl(cmd.url)
                if cmd.label is not None:
                    feed.label = ArticleTitle(cmd.label)
                if cmd.language is not None:
                    feed.language = Language(cmd.language)

                # Actualizar sync_policy si algún campo de sync cambió
                if (
                    cmd.sync_mode is not None
                    or cmd.sync_interval_minutes is not None
                    or cmd.sync_max_retries is not None
                ):
                    new_policy = SyncPolicy(
                        mode=(
                            SyncMode(cmd.sync_mode)
                            if cmd.sync_mode
                            else feed.sync_policy.mode
                        ),
                        interval_minutes=(
                            cmd.sync_interval_minutes
                            if cmd.sync_interval_minutes is not None
                            else feed.sync_policy.interval_minutes
                        ),
                        max_retries=(
                            cmd.sync_max_retries
                            if cmd.sync_max_retries is not None
                            else feed.sync_policy.max_retries
                        ),
                        backoff_multiplier=feed.sync_policy.backoff_multiplier,
                        max_backoff_minutes=feed.sync_policy.max_backoff_minutes,
                        timeout_seconds=feed.sync_policy.timeout_seconds,
                        max_items_per_run=feed.sync_policy.max_items_per_run,
                    )
                    feed.update_sync_policy(new_policy)

                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_pause_feed(self, cmd: PauseFeedCommand) -> Result[FeedDetailDTO]:
        """Pausa un Feed.

        Marca el feed como inactivo. Requiere reactivación manual.
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                feed.pause(cmd.reason)
                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_activate_feed(
        self, cmd: ActivateFeedCommand
    ) -> Result[FeedDetailDTO]:
        """Reactivar un feed previamente pausado.

        Resetea retry_count a 0 y marca como activo.
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                feed.activate()
                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_record_collection(
        self, cmd: RecordCollectionCommand
    ) -> Result[FeedDetailDTO]:
        """Registra un fetch exitoso.

        Resetea retry_count a 0. Emite evento si count > 0.
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                batch_id = UUID(cmd.batch_id) if cmd.batch_id else None
                feed.record_collection(batch_id=batch_id, count=cmd.count)

                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: publish events
                events = feed.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_record_failure(
        self, cmd: RecordFailureCommand
    ) -> Result[FeedDetailDTO]:
        """Registra un fallo de fetch.

        Incrementa retry_count. Si excede max_retries, auto-pausa.
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                feed.record_failure(cmd.error)

                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events (record_failure no emite eventos)
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_assign_category_to_feed(
        self, cmd: AssignCategoryToFeedCommand
    ) -> Result[FeedDetailDTO]:
        """Asigna una categoría existente a un Feed."""
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

                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                feed.assign_category(category_id)
                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_assign_topic_to_feed(
        self, cmd: AssignTopicToFeedCommand
    ) -> Result[FeedDetailDTO]:
        """Asigna un topic existente a un Feed."""
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

                feed_id = FeedId.from_string(cmd.feed_id)
                result = self._feed_repo.find_by_id(feed_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                feed = result.value

                feed.assign_topic(topic_id)
                self._feed_repo.save(feed)
                self._uow.commit()

                # After commit: pull events
                feed.pull_events()

                return Result.success(FeedMapper.to_detail(feed))

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

    def execute_find_feed(self, query: FindFeedQuery) -> Result[FeedDetailDTO]:
        """Busca un Feed por ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            feed_id = FeedId.from_string(query.feed_id)
            result = self._feed_repo.find_by_id(feed_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(FeedMapper.to_detail(result.value))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )

    def execute_list_feeds(
        self, query: ListFeedsQuery
    ) -> Result[QueryResult[FeedSummaryDTO]]:
        """Lista feeds de un NewsSource con paginación.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            source_id = SourceId.from_string(query.source_id)
            feeds = self._feed_repo.find_by_source(source_id)
            dtos = [FeedMapper.to_summary(f) for f in feeds]
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
