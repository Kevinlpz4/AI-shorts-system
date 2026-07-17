"""
Score Commands — operaciones de ajuste de pesos y recálculo de señales.

Commands:
    - AdjustScoreWeightsCommand: Ajustar pesos de scoring del LearningModel.
    - RecalculateSignalsCommand: Recalcular señales de aprendizaje.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdjustScoreWeightsCommand:
    """Ajustar pesos de scoring del LearningModel.

    Attributes:
        source_id: ID del LearningModel a ajustar.
        weights: Nuevos pesos de scoring (relevance, popularity, recency, source_reliability).
        reason: Razón del ajuste (requerida).
    """

    source_id: str
    weights: dict[str, float]
    reason: str


@dataclass(frozen=True)
class RecalculateSignalsCommand:
    """Recalcular señales de aprendizaje.

    Si se provee source_id, recalcula solo para esa fuente.
    Si se provee signal_type, filtra por tipo de señal.

    Attributes:
        source_id: ID de la fuente para filtrar (opcional).
        signal_type: Tipo de señal para filtrar (opcional).
    """

    source_id: str | None = None
    signal_type: str | None = None
