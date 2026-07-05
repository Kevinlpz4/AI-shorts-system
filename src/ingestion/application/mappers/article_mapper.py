"""
RawArticleMapper — convierte ``RawArticle`` (domain) → ``RawArticleSummaryDTO`` / ``RawArticleDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""

from __future__ import annotations

from ingestion.application.dto.article_dto import (
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
)
from ingestion.domain.entities.raw_article import RawArticle


class RawArticleMapper:
    """Mapea entidades RawArticle a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: RawArticle) -> RawArticleSummaryDTO:
        """Convierte una entidad RawArticle a RawArticleSummaryDTO.

        Excluye content_hash y metadata (información interna).

        Args:
            entity: Entidad de dominio RawArticle.

        Returns:
            RawArticleSummaryDTO con datos públicos.
        """
        return RawArticleSummaryDTO(
            id=str(entity.id),
            feed_id=str(entity.feed_id),
            title=entity.title.value,
            url=entity.url.value,
            author=entity.author,
            language=entity.language.code if entity.language else None,
            published_at=entity.published_at,
            fetched_at=entity.fetched_at,
        )

    @staticmethod
    def to_detail(entity: RawArticle) -> RawArticleDetailDTO:
        """Convierte una entidad RawArticle a RawArticleDetailDTO.

        Incluye todos los campos del artículo.

        Args:
            entity: Entidad de dominio RawArticle.

        Returns:
            RawArticleDetailDTO con datos completos.
        """
        return RawArticleDetailDTO(
            id=str(entity.id),
            feed_id=str(entity.feed_id),
            external_id=entity.external_id,
            content_hash=entity.content_hash,
            title=entity.title.value,
            url=entity.url.value,
            author=entity.author,
            language=entity.language.code if entity.language else None,
            published_at=entity.published_at,
            fetched_at=entity.fetched_at,
            content_preview=entity.content_preview,
            metadata=entity.metadata,
        )
