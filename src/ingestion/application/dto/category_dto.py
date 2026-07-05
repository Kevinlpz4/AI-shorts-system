"""
Category DTOs — representaciones de datos de Category.

DTOs:
    - CategorySummaryDTO: Vista resumida (sin parent).
    - CategoryDetailDTO: Vista completa con parent_id.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySummaryDTO:
    """Resumen de una Category.

    Attributes:
        id: ID único de la categoría.
        name: Nombre legible de la categoría.
        slug: Slug URL-friendly, único globalmente.
        is_active: Si está habilitada.
    """

    id: str
    name: str
    slug: str
    is_active: bool


@dataclass(frozen=True)
class CategoryDetailDTO:
    """Detalle completo de una Category.

    Attributes:
        id: ID único de la categoría.
        name: Nombre legible de la categoría.
        slug: Slug URL-friendly, único globalmente.
        parent_id: ID de la categoría padre (opcional).
        is_active: Si está habilitada.
    """

    id: str
    name: str
    slug: str
    parent_id: str | None = None
    is_active: bool = True
