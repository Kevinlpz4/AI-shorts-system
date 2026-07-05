"""
Article Queries — consultas para RawArticle.

Queries:
    - FindArticleQuery: Buscar artículo por ID.
    - ListArticlesQuery: Listar artículos por feed con paginación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindArticleQuery:
    """Buscar un RawArticle por su ID.

    Attributes:
        article_id: ID del artículo a buscar.
    """

    article_id: str


@dataclass(frozen=True)
class ListArticlesQuery:
    """Listar artículos de un Feed con paginación.

    Attributes:
        feed_id: ID del Feed fuente.
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    feed_id: str
    page: int = 1
    size: int = 50
