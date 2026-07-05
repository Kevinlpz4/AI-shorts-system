"""
RawArticle DTOs — representaciones de datos de RawArticle.

DTOs:
    - RawArticleSummaryDTO: Vista resumida (sin hash ni metadata).
    - RawArticleDetailDTO: Vista completa con todos los campos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RawArticleSummaryDTO:
    """Resumen de un RawArticle.

    Attributes:
        id: ID único del artículo.
        feed_id: ID del Feed del que se obtuvo.
        title: Título del artículo.
        url: URL canónica del artículo.
        author: Autor o creador (opcional).
        language: Código ISO 639-1 del idioma (opcional).
        published_at: Fecha de publicación original (opcional).
        fetched_at: Momento en que se obtuvo (opcional).
    """

    id: str
    feed_id: str
    title: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None


@dataclass(frozen=True)
class RawArticleDetailDTO:
    """Detalle completo de un RawArticle.

    Attributes:
        id: ID único del artículo.
        feed_id: ID del Feed del que se obtuvo.
        external_id: ID único en el sistema externo.
        content_hash: SHA-256 del contenido (64 caracteres hex).
        title: Título del artículo.
        url: URL canónica del artículo.
        author: Autor o creador (opcional).
        language: Código ISO 639-1 del idioma (opcional).
        published_at: Fecha de publicación original (opcional).
        fetched_at: Momento en que se obtuvo (opcional).
        content_preview: Extracto o resumen corto (opcional).
        metadata: Datos adicionales del proveedor (opcional).
    """

    id: str
    feed_id: str
    external_id: str
    content_hash: str
    title: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None
    content_preview: str | None = None
    metadata: dict | None = None
