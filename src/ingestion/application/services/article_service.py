"""
ArticleService — Casos de uso para RawArticle.

Orquesta la creación y consulta del aggregate RawArticle (inmutable),
aplicando la regla AL-05 (feed_id referencia Feed existente).

Dependencias inyectadas (DIP):
    - raw_article_repo: RawArticleRepository
    - feed_repo: FeedRepository
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

from ingestion.application.dto.article_dto import (
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
)
from ingestion.application.errors.error_mapper import ErrorMapper
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.application.mappers.article_mapper import RawArticleMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.article_queries import (
    FindArticleQuery,
    ListArticlesQuery,
)
from ingestion.application.commands.article_commands import CreateRawArticleCommand
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.entities.ids import FeedId, RawArticleId
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.ports.repositories import FeedRepository, RawArticleRepository
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language


class ArticleService:
    """Casos de uso para RawArticle.

    Todos los métodos retornan ``Result[RawArticleDetailDTO]`` o
    ``Result[QueryResult[RawArticleSummaryDTO]]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        raw_article_repo: RawArticleRepository,
        feed_repo: FeedRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._raw_article_repo = raw_article_repo
        self._feed_repo = feed_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    # ── Commands ──

    def execute_create_article(
        self, cmd: CreateRawArticleCommand
    ) -> Result[RawArticleDetailDTO]:
        """Crea un nuevo RawArticle.

        Reglas:
            - AL-05: feed_id debe referenciar un Feed existente.
            - URL única dentro del mismo feed.
            - content_hash único dentro del mismo feed.
        """
        with self._uow:
            try:
                feed_id = FeedId.from_string(cmd.feed_id)

                # AL-05: feed_id debe referenciar un Feed existente
                feed_result = self._feed_repo.find_by_id(feed_id)
                if feed_result.is_failure:
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.FEED_NOT_FOUND,
                            message=f"Feed '{cmd.feed_id}' not found",
                        )
                    )

                # Verificar URL única dentro del feed
                if self._raw_article_repo.exists_by_url(
                    feed_id, ArticleUrl(cmd.url)
                ):
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.DUPLICATE_ARTICLE,
                            message=f"Article URL '{cmd.url}' already exists in feed",
                        )
                    )

                # Verificar hash único dentro del feed
                if self._raw_article_repo.exists_by_hash(
                    feed_id, cmd.content_hash
                ):
                    return Result.failure(
                        Error(
                            code=IngestionErrorCode.DUPLICATE_ARTICLE,
                            message="Article with same content hash already exists in feed",
                        )
                    )

                # Construir RawArticle (inmutable)
                article = RawArticle(
                    id=RawArticleId.generate(),
                    feed_id=feed_id,
                    external_id=cmd.external_id,
                    content_hash=cmd.content_hash,
                    title=ArticleTitle(cmd.title),
                    url=ArticleUrl(cmd.url),
                    author=cmd.author,
                    language=Language(cmd.language) if cmd.language else None,
                    published_at=cmd.published_at,
                    fetched_at=cmd.fetched_at or self._clock.now(),
                    content_preview=cmd.content_preview,
                    metadata=cmd.metadata,
                )

                self._raw_article_repo.save(article)
                self._uow.commit()

                # RawArticle es inmutable — no tiene pull_events()
                # Solo mapeamos a DTO
                return Result.success(RawArticleMapper.to_detail(article))

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

    def execute_find_article(
        self, query: FindArticleQuery
    ) -> Result[RawArticleDetailDTO]:
        """Busca un RawArticle por ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            article_id = RawArticleId.from_string(query.article_id)
            result = self._raw_article_repo.find_by_id(article_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(RawArticleMapper.to_detail(result.value))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )

    def execute_list_articles(
        self, query: ListArticlesQuery
    ) -> Result[QueryResult[RawArticleSummaryDTO]]:
        """Lista artículos de un Feed con paginación.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            feed_id = FeedId.from_string(query.feed_id)
            articles = self._raw_article_repo.find_by_feed(
                feed_id, page=query.page, size=query.size
            )
            total = self._raw_article_repo.count_by_feed(feed_id)
            dtos = [RawArticleMapper.to_summary(a) for a in articles]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=total,
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
