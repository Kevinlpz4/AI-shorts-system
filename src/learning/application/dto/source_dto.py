"""
Source DTOs — representaciones de datos de SourceQualityProfile.

DTOs:
    - SourceQualityDTO: Vista completa del perfil de calidad de una fuente.
    - KeywordStatDTO: Estadísticas de un keyword específico.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordStatDTO:
    """Estadísticas de un keyword específico.

    Attributes:
        keyword: El keyword being tracked.
        count: Número total de veces que apareció en contenido.
        approved_count: Número de veces que fue aprobado.
        approval_rate: Tasa de aprobación (0.0 si no hay datos).
    """

    keyword: str
    count: int
    approved_count: int
    approval_rate: float


@dataclass(frozen=True)
class SourceQualityDTO:
    """Perfil de calidad de una fuente de contenido.

    Attributes:
        source_name: Nombre de la fuente.
        total_decisions: Número total de decisiones para esta fuente.
        approved: Número de aprobaciones humanas.
        rejected: Número de rechazos humanos.
        overridden: Número de decisiones sobreescritas.
        approval_rate: Tasa de aprobación (approved / total).
        keyword_stats: Estadísticas por keyword.
    """

    source_name: str
    total_decisions: int
    approved: int
    rejected: int
    overridden: int
    approval_rate: float
    keyword_stats: tuple[KeywordStatDTO, ...] = ()
