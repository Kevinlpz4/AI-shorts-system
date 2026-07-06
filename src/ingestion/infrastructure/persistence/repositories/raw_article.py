"""
SQLAlchemyRawArticleRepository — implementación SQLAlchemy del puerto
``RawArticleRepository`` para el aggregate root inmutable ``RawArticle``.

La detección de duplicados usa las UNIQUE constraints de la BD:
    - (feed_id, external_id)
    - (feed_id, content_hash)
"""

from __future__ import annotations

from foundation.result.result import Error, Result
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.ids import FeedId, RawArticleId
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.infrastructure.persistence.exceptions import (
    DuplicateEntityError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import RawArticleModel


class SQLAlchemyRawArticleRepository:
    """SQLAlchemy repository para ``RawArticle`` (inmutable).

    Args:
        session: SQLAlchemy ``Session`` (gestionada externamente).
    """

    def __init__(self, session) -> None:
        self._session = session
        # Strong reference cache: prevents WeakInstanceDict invalidation.
        self._loaded: dict[str, RawArticleModel] = {}

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(model: RawArticleModel) -> RawArticle:
        """Convierte ORM Model → Domain Entity."""
        return RawArticle(
            id=model.id,
            feed_id=model.feed_id,
            external_id=model.external_id,
            content_hash=model.content_hash,
            title=model.title,
            url=model.url,
            author=model.author,
            language=model.language,
            published_at=model.published_at,
            fetched_at=model.fetched_at,
            content_preview=model.content_preview,
            metadata=model.provider_metadata,
        )

    @staticmethod
    def _to_model(article: RawArticle) -> RawArticleModel:
        """Crea un ORM Model desde Domain Entity."""
        return RawArticleModel(
            id=article.id,
            feed_id=article.feed_id,
            external_id=article.external_id,
            content_hash=article.content_hash,
            title=article.title,
            url=article.url,
            author=article.author,
            language=article.language,
            published_at=article.published_at,
            fetched_at=article.fetched_at,
            content_preview=article.content_preview,
            provider_metadata=article.metadata,
        )

    # ── Public API ───────────────────────────────────────────────────────────

    def save(self, article: RawArticle) -> None:
        """Persiste un RawArticle (siempre es creación, nunca actualización).

        Raises:
            DuplicateEntityError: Si ya existe un artículo con el mismo
                external_id+feed_id o content_hash+feed_id.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        model = self._to_model(article)
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "RawArticle",
                "external_id/content_hash",
                f"{article.external_id}/{article.content_hash}",
            ) from exc
        except StaleDataError as exc:
            raise DuplicateEntityError(
                "RawArticle",
                "external_id/content_hash",
                f"{article.external_id}/{article.content_hash}",
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save RawArticle {article.id}: {exc}",
            ) from exc

    def save_batch(self, articles: list[RawArticle]) -> None:
        """Persiste múltiples RawArticles en una operación atómica.

        Raises:
            DuplicateEntityError: Si algún artículo es duplicado.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        try:
            for article in articles:
                model = self._to_model(article)
                self._session.add(model)
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "RawArticle",
                "external_id/content_hash",
                "(batch)",
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save batch of {len(articles)} articles: {exc}",
            ) from exc

    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]:
        """Busca un RawArticle por su identidad única."""
        try:
            model = self._session.get(RawArticleModel, id)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
                        message=f"Article '{id}' not found",
                    ),
                )
            # Keep strong reference: prevents WeakInstanceDict invalidation.
            self._loaded[str(id)] = model
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find RawArticle {id}: {exc}",
            ) from exc

    def find_by_feed(
        self, feed_id: FeedId, page: int = 1, size: int = 50,
    ) -> list[RawArticle]:
        """Retorna RawArticles de un Feed con paginación."""
        try:
            stmt = (
                select(RawArticleModel)
                .where(RawArticleModel.feed_id == feed_id)
                .order_by(RawArticleModel.fetched_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find articles by feed {feed_id}: {exc}",
            ) from exc

    def find_by_hash(
        self, feed_id: FeedId, content_hash: str,
    ) -> Result[RawArticle]:
        """Busca un RawArticle por su content_hash dentro de un Feed."""
        try:
            stmt = (
                select(RawArticleModel)
                .where(
                    RawArticleModel.feed_id == feed_id,
                    RawArticleModel.content_hash == content_hash,
                )
                .limit(1)
            )
            model = self._session.scalar(stmt)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
                        message="Article not found",
                    ),
                )
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find article by hash: {exc}",
            ) from exc

    def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool:
        """Verifica si existe un RawArticle con esa URL en el Feed."""
        try:
            stmt = (
                select(RawArticleModel.id)
                .where(
                    RawArticleModel.feed_id == feed_id,
                    RawArticleModel.url == url,
                )
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check article existence by URL: {exc}",
            ) from exc

    def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool:
        """Verifica si existe un RawArticle con ese hash en el Feed."""
        try:
            stmt = (
                select(RawArticleModel.id)
                .where(
                    RawArticleModel.feed_id == feed_id,
                    RawArticleModel.content_hash == content_hash,
                )
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check article existence by hash: {exc}",
            ) from exc

    def count_by_feed(self, feed_id: FeedId) -> int:
        """Retorna la cantidad total de RawArticles de un Feed."""
        try:
            stmt = (
                select(func.count(RawArticleModel.id))
                .where(RawArticleModel.feed_id == feed_id)
            )
            result = self._session.scalar(stmt)
            return result if result is not None else 0
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to count articles by feed {feed_id}: {exc}",
            ) from exc
