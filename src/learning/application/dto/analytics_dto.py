"""
Analytics DTO — representación de analíticas del sistema de aprendizaje.

DTOs:
    - AnalyticsDTO: Analíticas generales del sistema.
"""
from __future__ import annotations

from dataclasses import dataclass

from learning.application.dto.source_dto import SourceQualityDTO


@dataclass(frozen=True)
class AnalyticsDTO:
    """Analíticas generales del sistema de aprendizaje.

    Attributes:
        total_feedback: Número total de feedback records.
        total_signals: Número total de señales de aprendizaje.
        average_approval_rate: Tasa de aprobación promedio (0.0-1.0).
        signals_by_dimension: Conteo de señales por dimensión (KEYWORD, SOURCE, etc.).
        top_sources: Fuentes con mejor rendimiento.
    """

    total_feedback: int
    total_signals: int
    average_approval_rate: float
    signals_by_dimension: dict[str, int]
    top_sources: tuple[SourceQualityDTO, ...]
