"""
Topic DTOs — representaciones de datos de Topic.

DTOs:
    - TopicSummaryDTO: Vista resumida (sin description).
    - TopicDetailDTO: Vista completa con description.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicSummaryDTO:
    """Resumen de un Topic.

    Attributes:
        id: ID único del topic.
        name: Nombre del topic, único globalmente.
        is_active: Si está habilitado.
    """

    id: str
    name: str
    is_active: bool


@dataclass(frozen=True)
class TopicDetailDTO:
    """Detalle completo de un Topic.

    Attributes:
        id: ID único del topic.
        name: Nombre del topic, único globalmente.
        description: Descripción opcional del topic.
        is_active: Si está habilitado.
    """

    id: str
    name: str
    description: str | None = None
    is_active: bool = True
