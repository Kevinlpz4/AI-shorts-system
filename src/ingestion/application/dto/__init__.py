"""
Application DTOs — 10 Data Transfer Objects inmutables para el BC Ingestion.

Cada DTO es un ``@dataclass(frozen=True)`` con solo tipos primitivos
y otros DTOs. No dependen de entidades de dominio.

Uso::

    from ingestion.application.dto import (
        SourceSummaryDTO,
        SourceDetailDTO,
    )
"""
from __future__ import annotations

from ingestion.application.dto.article_dto import (
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
)
from ingestion.application.dto.category_dto import (
    CategoryDetailDTO,
    CategorySummaryDTO,
)
from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
from ingestion.application.dto.topic_dto import TopicDetailDTO, TopicSummaryDTO

__all__ = [
    "SourceSummaryDTO",
    "SourceDetailDTO",
    "FeedSummaryDTO",
    "FeedDetailDTO",
    "RawArticleSummaryDTO",
    "RawArticleDetailDTO",
    "CategorySummaryDTO",
    "CategoryDetailDTO",
    "TopicSummaryDTO",
    "TopicDetailDTO",
]
