"""
SourceQualityMapper — convierte ``SourceQualityProfile`` (domain) → ``SourceQualityDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.source_dto import KeywordStatDTO, SourceQualityDTO
from learning.domain.entities.source_quality import SourceQualityProfile


class SourceQualityMapper:
    """Mapea entidades SourceQualityProfile a DTOs de aplicación."""

    @staticmethod
    def to_dto(entity: SourceQualityProfile) -> SourceQualityDTO:
        """Convierte una entidad SourceQualityProfile a SourceQualityDTO.

        Args:
            entity: Entidad de dominio SourceQualityProfile.

        Returns:
            SourceQualityDTO con datos del perfil de calidad.
        """
        # Map keywords dict to tuple of KeywordStatDTO
        keyword_stats: tuple[KeywordStatDTO, ...] = tuple(
            KeywordStatDTO(
                keyword=stat.keyword,
                count=stat.count,
                approved_count=stat.approved_count,
                approval_rate=stat.approval_rate,
            )
            for stat in entity.keywords.values()
        )

        return SourceQualityDTO(
            source_name=entity.source_name,
            total_decisions=entity.total_decisions,
            approved=entity.approved_count,
            rejected=entity.rejected_count,
            overridden=entity.overridden_count,
            approval_rate=entity.approval_rate,
            keyword_stats=keyword_stats,
        )
