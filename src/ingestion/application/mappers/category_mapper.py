"""
CategoryMapper — convierte ``Category`` (domain) → ``CategorySummaryDTO`` / ``CategoryDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""

from __future__ import annotations

from ingestion.application.dto.category_dto import CategoryDetailDTO, CategorySummaryDTO
from ingestion.domain.entities.category import Category


class CategoryMapper:
    """Mapea entidades Category a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: Category) -> CategorySummaryDTO:
        """Convierte una entidad Category a CategorySummaryDTO.

        Excluye parent_id (relación jerárquica).

        Args:
            entity: Entidad de dominio Category.

        Returns:
            CategorySummaryDTO con datos básicos.
        """
        return CategorySummaryDTO(
            id=str(entity.id),
            name=entity.name.value,
            slug=entity.slug,
            is_active=entity.is_active,
        )

    @staticmethod
    def to_detail(entity: Category) -> CategoryDetailDTO:
        """Convierte una entidad Category a CategoryDetailDTO.

        Incluye parent_id.

        Args:
            entity: Entidad de dominio Category.

        Returns:
            CategoryDetailDTO con datos completos.
        """
        return CategoryDetailDTO(
            id=str(entity.id),
            name=entity.name.value,
            slug=entity.slug,
            parent_id=str(entity.parent_id) if entity.parent_id else None,
            is_active=entity.is_active,
        )
