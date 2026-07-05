"""
Article Commands — creación de RawArticle.

Commands:
    - CreateRawArticleCommand: Crear nuevo artículo crudo e inmutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateRawArticleCommand:
    """Crear un nuevo RawArticle a partir de datos obtenidos de un Feed.

    El artículo es inmutable una vez creado (I-11).

    La validación de integridad (content_hash, fechas) se realiza en
    el constructor de la entidad ``RawArticle`` (domain).

    Attributes:
        feed_id: ID del Feed del que se obtuvo.
        external_id: ID único en el sistema externo.
        content_hash: SHA-256 del contenido (64 caracteres hex).
        title: Título del artículo.
        url: URL canónica del artículo.
        author: Autor o creador (opcional).
        language: Código ISO 639-1 del idioma (opcional).
        published_at: Fecha de publicación original (opcional).
        fetched_at: Momento en que se obtuvo (opcional, default: UTC now).
        content_preview: Extracto o resumen corto (opcional).
        metadata: Datos adicionales del proveedor (opcional).
    """

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
