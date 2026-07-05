"""
FeedMapper — convierte ``Feed`` (domain) → ``FeedSummaryDTO`` / ``FeedDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""

from __future__ import annotations

from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.domain.entities.feed import Feed


class FeedMapper:
    """Mapea entidades Feed a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: Feed) -> FeedSummaryDTO:
        """Convierte una entidad Feed a FeedSummaryDTO.

        Args:
            entity: Entidad de dominio Feed.

        Returns:
            FeedSummaryDTO con datos básicos.
        """
        return FeedSummaryDTO(
            id=str(entity.id),
            source_id=str(entity.source_id),
            url=entity.url.value,
            label=entity.label.value,
            language=entity.language.code,
            is_active=entity.is_active,
            retry_count=entity.retry_count,
        )

    @staticmethod
    def to_detail(entity: Feed) -> FeedDetailDTO:
        """Convierte una entidad Feed a FeedDetailDTO.

        Incluye sync_policy, categorías y topics.

        Args:
            entity: Entidad de dominio Feed.

        Returns:
            FeedDetailDTO con datos completos.
        """
        return FeedDetailDTO(
            id=str(entity.id),
            source_id=str(entity.source_id),
            url=entity.url.value,
            label=entity.label.value,
            language=entity.language.code,
            is_active=entity.is_active,
            sync_mode=entity.sync_policy.mode.value,
            sync_interval_minutes=entity.sync_policy.interval_minutes,
            sync_max_retries=entity.sync_policy.max_retries,
            categories=tuple(str(cid) for cid in entity.categories),
            topics=tuple(str(tid) for tid in entity.topics),
            retry_count=entity.retry_count,
        )
