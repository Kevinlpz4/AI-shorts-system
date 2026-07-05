"""
TopicMapper — convierte ``Topic`` (domain) → ``TopicSummaryDTO`` / ``TopicDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""

from __future__ import annotations

from ingestion.application.dto.topic_dto import TopicDetailDTO, TopicSummaryDTO
from ingestion.domain.entities.topic import Topic


class TopicMapper:
    """Mapea entidades Topic a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: Topic) -> TopicSummaryDTO:
        """Convierte una entidad Topic a TopicSummaryDTO.

        Excluye description.

        Args:
            entity: Entidad de dominio Topic.

        Returns:
            TopicSummaryDTO con datos básicos.
        """
        return TopicSummaryDTO(
            id=str(entity.id),
            name=entity.name,
            is_active=entity.is_active,
        )

    @staticmethod
    def to_detail(entity: Topic) -> TopicDetailDTO:
        """Convierte una entidad Topic a TopicDetailDTO.

        Incluye description.

        Args:
            entity: Entidad de dominio Topic.

        Returns:
            TopicDetailDTO con datos completos.
        """
        return TopicDetailDTO(
            id=str(entity.id),
            name=entity.name,
            description=entity.description,
            is_active=entity.is_active,
        )
