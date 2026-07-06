"""
SQLAlchemyTopicRepository — implementación SQLAlchemy del puerto
``TopicRepository`` para la entidad ``Topic``.

Topic es la entidad más simple: sin VOs propios, sin FKs, sin jerarquía.
"""

from __future__ import annotations

from foundation.result.result import Error, Result
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.ids import TopicId
from ingestion.domain.entities.topic import Topic
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.infrastructure.persistence.exceptions import (
    ConcurrentModificationError,
    DuplicateEntityError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import TopicModel


class SQLAlchemyTopicRepository:
    """SQLAlchemy repository para ``Topic`` entities.

    Args:
        session: SQLAlchemy ``Session`` (gestionada externamente).
    """

    def __init__(self, session) -> None:
        self._session = session
        # Strong reference cache: prevents WeakInstanceDict invalidation.
        self._loaded: dict[str, TopicModel] = {}

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(model: TopicModel) -> Topic:
        """Convierte ORM Model → Domain Entity."""
        return Topic(
            id=model.id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_model(entity: Topic) -> TopicModel:
        """Crea un ORM Model desde Domain Entity."""
        return TopicModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            is_active=entity.is_active,
        )

    # ── Public API ───────────────────────────────────────────────────────────

    def save(self, topic: Topic) -> None:
        """Persiste un Topic (crea o actualiza).

        Raises:
            DuplicateEntityError: Si viola un UNIQUE constraint (name).
            ConcurrentModificationError: Si hay conflicto de optimistic lock.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        try:
            key = str(topic.id)
            existing = self._loaded.get(key)
            if existing is None:
                existing = self._session.get(TopicModel, topic.id)
            if existing is None:
                model = self._to_model(topic)
                self._session.add(model)
                self._loaded[key] = model
            else:
                existing.name = topic.name
                existing.description = topic.description
                existing.is_active = topic.is_active

            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "Topic", "name", topic.name,
            ) from exc
        except StaleDataError as exc:
            raise ConcurrentModificationError(
                "Topic", str(topic.id),
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save Topic {topic.id}: {exc}",
            ) from exc

    def find_by_id(self, id: TopicId) -> Result[Topic]:
        """Busca un Topic por su identidad única."""
        try:
            model = self._session.get(TopicModel, id)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.TOPIC_NOT_FOUND,
                        message=f"Topic '{id}' not found",
                    ),
                )
            # Keep strong reference: prevents WeakInstanceDict invalidation.
            self._loaded[str(id)] = model
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Topic {id}: {exc}",
            ) from exc

    def find_by_name(self, name: str) -> Result[Topic]:
        """Busca un Topic por su nombre único."""
        try:
            stmt = (
                select(TopicModel)
                .where(TopicModel.name == name)
                .limit(1)
            )
            model = self._session.scalar(stmt)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.TOPIC_NOT_FOUND,
                        message=f"Topic '{name}' not found",
                    ),
                )
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Topic by name '{name}': {exc}",
            ) from exc

    def find_all(self) -> list[Topic]:
        """Retorna todos los topics registrados."""
        try:
            stmt = select(TopicModel).order_by(TopicModel.name)
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find all topics: {exc}",
            ) from exc

    def find_active(self) -> list[Topic]:
        """Retorna solo los topics activos (is_active=True)."""
        try:
            stmt = (
                select(TopicModel)
                .where(TopicModel.is_active.is_(True))
                .order_by(TopicModel.name)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find active topics: {exc}",
            ) from exc

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un Topic con el nombre dado."""
        try:
            stmt = (
                select(TopicModel.id)
                .where(TopicModel.name == name)
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check topic existence by name '{name}': {exc}",
            ) from exc
