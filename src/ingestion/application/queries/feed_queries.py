"""
Feed Queries — consultas para Feed.

Queries:
    - FindFeedQuery: Buscar feed por ID.
    - ListFeedsQuery: Listar feeds por fuente con paginación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindFeedQuery:
    """Buscar un Feed por su ID.

    Attributes:
        feed_id: ID del feed a buscar.
    """

    feed_id: str


@dataclass(frozen=True)
class ListFeedsQuery:
    """Listar feeds de un NewsSource con paginación.

    Attributes:
        source_id: ID del NewsSource padre.
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    source_id: str
    page: int = 1
    size: int = 50
