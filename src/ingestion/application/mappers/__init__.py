"""
Application Mappers — convierten entidades de dominio a DTOs de aplicación.

Cada mapper convierte en una sola dirección: Domain Entity → DTO.
No realizan persistencia, no ejecutan reglas, no llaman repositorios.

Uso::

    from ingestion.application.mappers import SourceMapper

    dto = SourceMapper.to_summary(news_source)
    detail = SourceMapper.to_detail(news_source)
"""
from __future__ import annotations

from ingestion.application.mappers.article_mapper import RawArticleMapper
from ingestion.application.mappers.category_mapper import CategoryMapper
from ingestion.application.mappers.feed_mapper import FeedMapper
from ingestion.application.mappers.source_mapper import SourceMapper
from ingestion.application.mappers.topic_mapper import TopicMapper

__all__ = [
    "SourceMapper",
    "FeedMapper",
    "RawArticleMapper",
    "CategoryMapper",
    "TopicMapper",
]
