"""
Category Queries — consultas para Category.

Queries:
    - FindCategoryQuery: Buscar categoría por ID.
    - ListCategoriesQuery: Listar categorías con paginación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindCategoryQuery:
    """Buscar una Category por su ID.

    Attributes:
        category_id: ID de la categoría a buscar.
    """

    category_id: str


@dataclass(frozen=True)
class ListCategoriesQuery:
    """Listar todas las Categories con paginación.

    Attributes:
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    page: int = 1
    size: int = 50
