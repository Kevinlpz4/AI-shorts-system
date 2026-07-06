"""
SQLAlchemyCategoryRepository — implementación SQLAlchemy del puerto
``CategoryRepository`` para la entidad ``Category``.

La jerarquía self-referencing se mapea via ``parent_id`` FK.
Las subcategorías se consultan por ``parent_id`` (no hay relación children).
"""

from __future__ import annotations

from foundation.result.result import Error, Result
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.category import Category
from ingestion.domain.entities.ids import CategoryId
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.infrastructure.persistence.exceptions import (
    ConcurrentModificationError,
    DuplicateEntityError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import CategoryModel


class SQLAlchemyCategoryRepository:
    """SQLAlchemy repository para ``Category`` entities.

    Args:
        session: SQLAlchemy ``Session`` (gestionada externamente).
    """

    def __init__(self, session) -> None:
        self._session = session
        # Strong reference cache: prevents WeakInstanceDict invalidation.
        self._loaded: dict[str, CategoryModel] = {}

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(model: CategoryModel) -> Category:
        """Convierte ORM Model → Domain Entity.
        NOTA: CategoryModel.description es una columna de infraestructura
        que el dominio NO conoce — se ignora en la conversión.
        """
        return Category(
            id=model.id,
            name=model.name,
            slug=model.slug,
            parent_id=model.parent_id,
            is_active=model.is_active,
        )

    @staticmethod
    def _to_model(entity: Category) -> CategoryModel:
        """Crea un ORM Model desde Domain Entity.
        CategoryModel.description no tiene equivalente en el dominio;
        el ORM lo setea como NULL (columna nullable).
        """
        return CategoryModel(
            id=entity.id,
            name=entity.name,
            slug=entity.slug,
            parent_id=entity.parent_id,
            is_active=entity.is_active,
        )

    # ── Public API ───────────────────────────────────────────────────────────

    def save(self, category: Category) -> None:
        """Persiste una Category (crea o actualiza).

        Raises:
            DuplicateEntityError: Si viola un UNIQUE constraint (slug).
            ConcurrentModificationError: Si hay conflicto de optimistic lock.
            PersistenceError: Para otros errores de infraestructura.

        NOTA: El manejo de la transacción (commit/rollback) es responsabilidad
        del UnitOfWork. Este repositorio solo ejecuta operaciones atómicas.
        """
        try:
            key = str(category.id)
            existing = self._loaded.get(key)
            if existing is None:
                existing = self._session.get(CategoryModel, category.id)
            if existing is None:
                model = self._to_model(category)
                self._session.add(model)
                self._loaded[key] = model
            else:
                existing.name = category.name
                existing.slug = category.slug
                existing.parent_id = category.parent_id
                existing.is_active = category.is_active

            self._session.flush()
        except IntegrityError as exc:
            raise DuplicateEntityError(
                "Category", "slug", category.slug or "",
            ) from exc
        except StaleDataError as exc:
            raise ConcurrentModificationError(
                "Category", str(category.id),
            ) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to save Category {category.id}: {exc}",
            ) from exc

    def find_by_id(self, id: CategoryId) -> Result[Category]:
        """Busca una Category por su identidad única."""
        try:
            model = self._session.get(CategoryModel, id)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                        message=f"Category '{id}' not found",
                    ),
                )
            # Keep strong reference: prevents WeakInstanceDict invalidation.
            self._loaded[str(id)] = model
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Category {id}: {exc}",
            ) from exc

    def find_by_slug(self, slug: str) -> Result[Category]:
        """Busca una Category por su slug único."""
        try:
            stmt = (
                select(CategoryModel)
                .where(CategoryModel.slug == slug)
                .limit(1)
            )
            model = self._session.scalar(stmt)
            if model is None:
                return Result.failure(
                    Error(
                        code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                        message=f"Category with slug '{slug}' not found",
                    ),
                )
            return Result.success(self._to_domain(model))
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find Category by slug '{slug}': {exc}",
            ) from exc

    def find_all(self) -> list[Category]:
        """Retorna todas las categorías registradas."""
        try:
            stmt = select(CategoryModel).order_by(CategoryModel.name)
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find all categories: {exc}",
            ) from exc

    def find_active(self) -> list[Category]:
        """Retorna solo las categorías activas (is_active=True)."""
        try:
            stmt = (
                select(CategoryModel)
                .where(CategoryModel.is_active.is_(True))
                .order_by(CategoryModel.name)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find active categories: {exc}",
            ) from exc

    def find_by_parent(self, parent_id: CategoryId) -> list[Category]:
        """Retorna las subcategorías directas de una categoría."""
        try:
            stmt = (
                select(CategoryModel)
                .where(CategoryModel.parent_id == parent_id)
                .order_by(CategoryModel.name)
            )
            models = self._session.scalars(stmt).all()
            return [self._to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to find categories by parent {parent_id}: {exc}",
            ) from exc

    def exists_by_slug(self, slug: str) -> bool:
        """Verifica si existe una categoría con el slug dado."""
        try:
            stmt = (
                select(CategoryModel.id)
                .where(CategoryModel.slug == slug)
                .limit(1)
            )
            return self._session.scalar(stmt) is not None
        except SQLAlchemyError as exc:
            raise PersistenceError(
                f"Failed to check category existence by slug '{slug}': {exc}",
            ) from exc
