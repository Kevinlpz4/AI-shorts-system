"""
RawArticle — Aggregate Root Inmutable del BC Ingestion.

Representa una pieza de contenido crudo obtenido de un Feed.
Es un registro de auditoría — una vez creado, nunca cambia.

TÉCNICAMENTE hereda de ``Entity`` (no de ``AggregateRoot``) por ser
inmutable y no emitir eventos. Ver ADR-023 para la justificación completa.

SE DOCUMENTA como Aggregate Root por razones de volumen y frontera de
consistencia en creación.

Invariantes:
  - I-11: IMMUTABLE — No modification after creation
  - I-12: external_id + feed_id MUST be unique (enforced by repository)
  - I-13: content_hash MUST be unique within the same Feed (enforced by repository)
  - I-14: fetched_at >= published_at (if published_at present)
  - I-15: title MUST NOT be empty (validated by ArticleTitle VO)
  - I-16: url MUST be a valid URL (validated by ArticleUrl VO)
  - I-17: content_hash MUST be a valid SHA-256 (64 hex chars)

Cross-AR rule (Application Layer):
  - AL-05: feed_id debe referenciar un Feed existente
"""

from __future__ import annotations

import re
from datetime import datetime

from foundation.base.entity import Entity

from ingestion.domain.entities.ids import FeedId, RawArticleId
from ingestion.domain.exceptions import InvalidStateError
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language

# Patrón para SHA-256: 64 caracteres hexadecimales en minúscula
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class RawArticle(Entity):
    """Artículo crudo e inmutable recolectado de un Feed.

    NOTA: Es TOTALMENTE inmutable. Una vez construido, ningún atributo
    puede modificarse (I-11). No usa @dataclass(frozen=True) porque
    Entity (parent) no es frozen — se implementa inmutabilidad manual
    mediante __setattr__.

    Attributes:
        id: Identidad única del artículo.
        feed_id: Feed del que se obtuvo (referencia por ID).
        external_id: ID único en el sistema externo.
        content_hash: SHA-256 del contenido (64 caracteres hex).
        title: Título del artículo (validado por ArticleTitle VO).
        url: URL canónica del artículo (validado por ArticleUrl VO).
        author: Autor o creador (opcional).
        language: Código ISO 639-1 del idioma (opcional).
        published_at: Fecha de publicación original (opcional).
        fetched_at: Momento en que se obtuvo el artículo.
        content_preview: Extracto o resumen corto (opcional, atributo plano).
        metadata: Datos adicionales del proveedor (dict plano).
    """

    def __init__(
        self,
        id: RawArticleId,
        feed_id: FeedId,
        external_id: str,
        content_hash: str,
        title: ArticleTitle,
        url: ArticleUrl,
        author: str | None = None,
        language: Language | None = None,
        published_at: datetime | None = None,
        fetched_at: datetime | None = None,
        content_preview: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Initialize an immutable RawArticle.

        Args:
            id: Identidad única del artículo.
            feed_id: Feed del que se obtuvo.
            external_id: ID único en el sistema externo.
            content_hash: SHA-256 del contenido (64 hex chars).
            title: Título del artículo.
            url: URL canónica del artículo.
            author: Autor o creador (opcional).
            language: Código ISO 639-1 del idioma (opcional).
            published_at: Fecha de publicación original (opcional).
            fetched_at: Momento en que se obtuvo.
            content_preview: Extracto o resumen (opcional).
            metadata: Datos adicionales (opcional).

        Raises:
            InvalidStateError: Si alguna invariante se viola.
        """
        # I-14: fetched_at >= published_at
        if published_at is not None and fetched_at is not None:
            if fetched_at < published_at:
                raise InvalidStateError(
                    "fetched_at must be >= published_at (I-14): "
                    f"fetched_at={fetched_at}, published_at={published_at}"
                )

        # I-17: content_hash must be valid SHA-256 (64 hex chars)
        if not _SHA256_PATTERN.match(content_hash):
            raise InvalidStateError(
                "content_hash must be a valid SHA-256 (64 hex chars) (I-17)"
            )

        # Use object.__setattr__ to set fields (immutability via __setattr__ override)
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "feed_id", feed_id)
        object.__setattr__(self, "external_id", external_id)
        object.__setattr__(self, "content_hash", content_hash)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "url", url)
        object.__setattr__(self, "author", author)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "published_at", published_at)
        object.__setattr__(self, "fetched_at", fetched_at)
        object.__setattr__(self, "content_preview", content_preview)
        object.__setattr__(self, "metadata", metadata)

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent mutation after construction (I-11)."""
        if hasattr(self, name):
            raise AttributeError(
                f"RawArticle is immutable (I-11): cannot modify '{name}'"
            )
        object.__setattr__(self, name, value)

    @property
    def article_url(self) -> ArticleUrl:
        """Accede al VO ArticleUrl encapsulado."""
        return self.url

    @property
    def article_title(self) -> ArticleTitle:
        """Accede al VO ArticleTitle encapsulado."""
        return self.title
