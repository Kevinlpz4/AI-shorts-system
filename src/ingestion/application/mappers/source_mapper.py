"""
SourceMapper — convierte ``NewsSource`` (domain) → ``SourceSummaryDTO`` / ``SourceDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""

from __future__ import annotations

from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
from ingestion.domain.entities.news_source import NewsSource


class SourceMapper:
    """Mapea entidades NewsSource a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: NewsSource) -> SourceSummaryDTO:
        """Convierte una entidad NewsSource a SourceSummaryDTO.

        Args:
            entity: Entidad de dominio NewsSource.

        Returns:
            SourceSummaryDTO con datos básicos.
        """
        return SourceSummaryDTO(
            id=str(entity.id),
            name=entity.name,
            source_type=entity.source_type.value,
            source_url=entity.source_url.value,
            is_active=entity.is_active,
        )

    @staticmethod
    def to_detail(entity: NewsSource) -> SourceDetailDTO:
        """Convierte una entidad NewsSource a SourceDetailDTO.

        Incluye IDs de categorías y topics asignados.

        Args:
            entity: Entidad de dominio NewsSource.

        Returns:
            SourceDetailDTO con datos completos.
        """
        return SourceDetailDTO(
            id=str(entity.id),
            name=entity.name,
            source_type=entity.source_type.value,
            source_url=entity.source_url.value,
            is_active=entity.is_active,
            categories=tuple(str(cid) for cid in entity.categories),
            topics=tuple(str(tid) for tid in entity.topics),
        )
