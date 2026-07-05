"""
ArticleUrl Value Object — URL canónica de un RawArticle.

Encapsula y valida la URL de un artículo individual obtenido de un Feed.
Provee normalización y extracción de dominio.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidArticleUrlError
from ingestion.domain.value_objects._url_base import validate_url


@dataclass(frozen=True)
class ArticleUrl(ValueObject):
    """URL canónica de un artículo individual.

    Attributes:
        value: La URL como string.

    Raises:
        InvalidArticleUrlError: Si la URL no pasa las validaciones.
    """

    value: str

    def __post_init__(self) -> None:
        """Validar la URL en construcción."""
        validate_url(
            self.value,
            error_cls=InvalidArticleUrlError,
            field_name="Article URL",
        )

    def normalized(self) -> str:
        """Retorna la URL canónica normalizada.

        Returns:
            URL normalizada como string.
        """
        parsed = urlparse(self.value.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") if parsed.path else ""
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{scheme}://{netloc}{path}{query}"

    def domain(self) -> str:
        """Extrae el dominio de la URL.

        Returns:
            El dominio (ej: "reddit.com", "news.ycombinator.com").
        """
        parsed = urlparse(self.value.strip())
        return parsed.netloc.lower()
