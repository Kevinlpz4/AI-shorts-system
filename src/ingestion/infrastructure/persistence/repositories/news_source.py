"""
SQLAlchemyNewsSourceRepository — implementación SQLAlchemy del puerto
``NewsSourceRepository`` para el aggregate root ``NewsSource``.

Encapsula el mapeo Domain → ORM y ORM → Domain completamente.
La capa Application nunca conoce ORM Models.
"""

from __future__ import annotations

from foundation.result.result import Error, Result
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.ids import SourceId
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.infrastructure.persistence.exceptions import (
    ConcurrentModificationError,
    DuplicateEntityError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import (
    NewsSourceModel,
    news_source_category_table,
    news_source_topic_table,
)


class SQLAlchemyNewsSourceRepository:
    """SQLAlchemy repository para ``NewsSource`` aggregate roots.

    Args:
        session: SQLAlchemy ``Session`` (gestionada externamente).
    """

    def __init__(self, session) -> None:
        self._session = session
        # Strong reference cache: SQLAlchemy 2.0 uses WeakInstanceDict, so
        # loaded models would be GC-collected when the repo method returns.
        # Keeping them here prevents identity map invalidation and ensures
        # save() can detect stale versions via the identity map.
        self._loaded: dict[str, NewsSourceModel] = {}

    # ── Mappers ──────────────────────────────────────────────────────────────

    def _to_domain(self, model: NewsSourceModel) -> NewsSource:
        """Convierte ORM Model → Domain Entity."""
        # Extract M:N IDs from loaded relationships
        categories = [cat.id for cat in (model.categories or [])]
        topics = [topic.id for topic in (model.topics or [])]

        return NewsSource(
            id=model.id,
            name=model.name,
            source_type=model.source_type,
            source_url=model.source_url,
            is_active=model.is_active,
            categories=categories,
            topics=topics,
        )

    def _to_model(self, entity: NewsSource) -> NewsSourceModel:
        """Crea un ORM Model desde Domain Entity (sin M:N)."""
        return NewsSourceModel(
            id=entity.id,
            name=entity.name,
            source_type=entity.source_type,
            source_url=entity.source_url,
            is_active=entity.is_active,
        )

    def _sync_m2m(self, entity: NewsSource) -> None:
        """Sincroniza relaciones M:N (categories, topics).

        Borra todas las asociaciones existentes y las reinserta.
        """
        # Categories
        self._session.execute(
            news_source_category_table.delete().where(
                news_source_category_table.c.source_id == entity.id,
            ),
        )
        for cat_id in entity.categories:
            self._session.execute(
                news_source_category_table.insert().values(
                    source_id=entity.id,
                    category_id=cat_id,
                ),
            )

        # Topics
        self._session.execute(
            news_source_topic_table.delete().where(
                news_source_topic_table.c.source_id == entity.id,
            ),
        )
        for topic_id in entity.topics:
            self._session.execute(
                news_source_topic_table.insert().values(
                    source_id=entity.id,
                    topic_id=topic_id,
                ),
            )

    # ── Public API ───────────────────────────────────────────────────────────

    def save(self, source: NewsSource) -> None:
        """Persiste un NewsSource (crea o actualiza).

        Raises:
            DuplicateEntityError: Si viola un UNIQUE constraint.
            ConcurrentModificationError: Si hay conflicto de optimistic lock.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        try:
            key = str(source.id)
            existing = self._loaded.get(key)
            if existing is None:
                existing = self._session.get(NewsSourceModel, source.id)
            if existing is None:
                model = self._to_model(source)
                self._session.add(model)
                self._loaded[key] = model
            else:
                existing.name = source.name
                existing.source_type = source.source_type
                existing.source_url = source.source_url
                existing.is_active = source.is_active

            self._sync_m2m(source)
            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "NewsSource", "name", source.name,
            ) from exc
        except StaleDataError as exc:
            raise ConcurrentModificationError(
                "NewsSource", str(source.id),
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save NewsSource {source.id}: {exc}",
            ) from exc

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        """Busca un NewsSource por su identidad única."""
        try:
            model = self._session.get(NewsSourceModel, id)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                        message=f"Source '{id}' not found",
                    ),
                )
            # Keep strong reference: prevents WeakInstanceDict invalidation
            # from clearing the identity map entry when this method returns.
            self._loaded[str(id)] = model
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find NewsSource {id}: {exc}",
            ) from exc

    def find_by_name(self, name: str) -> Result[NewsSource]:
        """Busca un NewsSource por su nombre único."""
        try:
            stmt = (
                select(NewsSourceModel)
                .where(NewsSourceModel.name == name)
                .limit(1)
            )
            model = self._session.scalar(stmt)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                        message=f"Source '{name}' not found",
                    ),
                )
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find NewsSource by name '{name}': {exc}",
            ) from exc

    def find_all(self) -> list[NewsSource]:
        """Retorna todos los NewsSources registrados."""
        try:
            stmt = select(NewsSourceModel).order_by(NewsSourceModel.name)
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find all NewsSources: {exc}",
            ) from exc

    def find_active(self) -> list[NewsSource]:
        """Retorna solo los NewsSources activos (is_active=True)."""
        try:
            stmt = (
                select(NewsSourceModel)
                .where(NewsSourceModel.is_active.is_(True))
                .order_by(NewsSourceModel.name)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find active NewsSources: {exc}",
            ) from exc

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un NewsSource con el nombre dado."""
        try:
            stmt = (
                select(NewsSourceModel.id)
                .where(NewsSourceModel.name == name)
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check existence by name '{name}': {exc}",
            ) from exc
