"""
Source DTOs — representaciones de datos de NewsSource.

DTOs:
    - SourceSummaryDTO: Vista resumida (sin relaciones).
    - SourceDetailDTO: Vista completa con IDs de categorías y topics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSummaryDTO:
    """Resumen de un NewsSource.

    Attributes:
        id: ID único de la fuente.
        name: Nombre legible de la fuente.
        source_type: Tipo de fuente (RSS, API, SOCIAL_MEDIA, NEWSLETTER).
        source_url: URL base de la fuente.
        is_active: Si está habilitada para ingesta.
    """

    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool


@dataclass(frozen=True)
class SourceDetailDTO:
    """Detalle completo de un NewsSource.

    Attributes:
        id: ID único de la fuente.
        name: Nombre legible de la fuente.
        source_type: Tipo de fuente.
        source_url: URL base de la fuente.
        is_active: Si está habilitada para ingesta.
        categories: IDs de categorías asignadas.
        topics: IDs de topics asignados.
    """

    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool
    categories: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
