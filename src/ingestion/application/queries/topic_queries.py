"""
Topic Queries — consultas para Topic.

Queries:
    - FindTopicQuery: Buscar topic por ID.
    - ListTopicsQuery: Listar topics con paginación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindTopicQuery:
    """Buscar un Topic por su ID.

    Attributes:
        topic_id: ID del topic a buscar.
    """

    topic_id: str


@dataclass(frozen=True)
class ListTopicsQuery:
    """Listar todos los Topics con paginación.

    Attributes:
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    page: int = 1
    size: int = 50
