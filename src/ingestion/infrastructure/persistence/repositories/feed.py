"""
SQLAlchemyFeedRepository — implementación SQLAlchemy del puerto
``FeedRepository`` para el aggregate root ``Feed``.

El ``SyncPolicy`` compuesto se mapea automáticamente via ``composite()``.
Las relaciones M:N (categories, topics) se sincronizan por tabla asociativa.
"""

from __future__ import annotations

from foundation.result.result import Error, Result
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import FeedId, SourceId
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.infrastructure.persistence.exceptions import (
    ConcurrentModificationError,
    DuplicateEntityError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import (
    FeedModel,
    feed_category_table,
    feed_topic_table,
)


class SQLAlchemyFeedRepository:
    """SQLAlchemy repository para ``Feed`` aggregate roots.

    Args:
        session: SQLAlchemy ``Session`` (gestionada externamente).
    """

    def __init__(self, session) -> None:
        self._session = session
        # Strong reference cache: prevents WeakInstanceDict invalidation
        # from clearing the identity map entry when methods return.
        self._loaded: dict[str, FeedModel] = {}

    # ── Mappers ──────────────────────────────────────────────────────────────

    def _to_domain(self, model: FeedModel) -> Feed:
        """Convierte ORM Model → Domain Entity."""
        categories = [cat.id for cat in (model.categories or [])]
        topics = [topic.id for topic in (model.topics or [])]

        return Feed(
            id=model.id,
            source_id=model.source_id,
            url=model.url,
            label=model.label,
            language=model.language,
            is_active=model.is_active,
            sync_policy=model.sync_policy,
            categories=categories,
            topics=topics,
            retry_count=model.retry_count,
        )

    def _to_model(self, entity: Feed) -> FeedModel:
        """Crea un ORM Model desde Domain Entity (sin SyncPolicy, sin M:N)."""
        model = FeedModel(
            id=entity.id,
            source_id=entity.source_id,
            url=entity.url,
            label=entity.label,
            language=entity.language,
            is_active=entity.is_active,
            retry_count=entity.retry_count,
        )
        # SyncPolicy via composite
        model.sync_policy = entity.sync_policy
        return model

    def _sync_m2m(self, entity: Feed) -> None:
        """Sincroniza relaciones M:N (categories, topics)."""
        # Categories
        self._session.execute(
            feed_category_table.delete().where(
                feed_category_table.c.feed_id == entity.id,
            ),
        )
        for cat_id in entity.categories:
            self._session.execute(
                feed_category_table.insert().values(
                    feed_id=entity.id,
                    category_id=cat_id,
                ),
            )

        # Topics
        self._session.execute(
            feed_topic_table.delete().where(
                feed_topic_table.c.feed_id == entity.id,
            ),
        )
        for topic_id in entity.topics:
            self._session.execute(
                feed_topic_table.insert().values(
                    feed_id=entity.id,
                    topic_id=topic_id,
                ),
            )

    # ── Public API ───────────────────────────────────────────────────────────

    def save(self, feed: Feed) -> None:
        """Persiste un Feed (crea o actualiza).

        Raises:
            DuplicateEntityError: Si viola un UNIQUE constraint.
            ConcurrentModificationError: Si hay conflicto de optimistic lock.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        try:
            key = str(feed.id)
            existing = self._loaded.get(key)
            if existing is None:
                existing = self._session.get(FeedModel, feed.id)
            if existing is None:
                model = self._to_model(feed)
                self._session.add(model)
                self._loaded[key] = model
            else:
                existing.source_id = feed.source_id
                existing.url = feed.url
                existing.label = feed.label
                existing.language = feed.language
                existing.is_active = feed.is_active
                existing.retry_count = feed.retry_count
                existing.sync_policy = feed.sync_policy

            self._sync_m2m(feed)
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "Feed", "source_id+url", f"{feed.source_id}+{feed.url}",
            ) from exc
        except StaleDataError as exc:
            raise ConcurrentModificationError(
                "Feed", str(feed.id),
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save Feed {feed.id}: {exc}",
            ) from exc

    def find_by_id(self, id: FeedId) -> Result[Feed]:
        """Busca un Feed por su identidad única."""
        try:
            model = self._session.get(FeedModel, id)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.FEED_NOT_FOUND,
                        message=f"Feed '{id}' not found",
                    ),
                )
            # Keep strong reference: prevents WeakInstanceDict invalidation.
            self._loaded[str(id)] = model
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Feed {id}: {exc}",
            ) from exc

    def find_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna todos los Feeds de un NewsSource."""
        try:
            stmt = (
                select(FeedModel)
                .where(FeedModel.source_id == source_id)
                .order_by(FeedModel.label)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Feeds by source {source_id}: {exc}",
            ) from exc

    def find_by_url(
        self, source_id: SourceId, url: ArticleUrl,
    ) -> Result[Feed]:
        """Busca un Feed por URL dentro de un NewsSource."""
        try:
            stmt = (
                select(FeedModel)
                .where(
                    FeedModel.source_id == source_id,
                    FeedModel.url == url,
                )
                .limit(1)
            )
            model = self._session.scalar(stmt)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.FEED_NOT_FOUND,
                        message="Feed not found",
                    ),
                )
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Feed by URL {url}: {exc}",
            ) from exc

    def find_active_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna los Feeds activos de un NewsSource."""
        try:
            stmt = (
                select(FeedModel)
                .where(
                    FeedModel.source_id == source_id,
                    FeedModel.is_active.is_(True),
                )
                .order_by(FeedModel.label)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find active Feeds by source {source_id}: {exc}",
            ) from exc

    def exists_by_source_and_url(
        self, source_id: SourceId, url: ArticleUrl,
    ) -> bool:
        """Verifica si existe un Feed con esa URL en el NewsSource."""
        try:
            stmt = (
                select(FeedModel.id)
                .where(
                    FeedModel.source_id == source_id,
                    FeedModel.url == url,
                )
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check Feed existence by URL {url}: {exc}",
            ) from exc

    def count_active_by_source(self, source_id: SourceId) -> int:
        """Cuenta los Feeds activos de un NewsSource."""
        try:
            stmt = (
                select(func.count(FeedModel.id))
                .where(
                    FeedModel.source_id == source_id,
                    FeedModel.is_active.is_(True),
                )
            )
            result = self._session.scalar(stmt)
            return result if result is not None else 0
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to count active Feeds by source {source_id}: {exc}",
            ) from exc
