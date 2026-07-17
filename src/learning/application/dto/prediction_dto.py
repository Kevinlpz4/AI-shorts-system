"""
Prediction DTO — representación de predicciones de aprobación.

DTOs:
    - PredictionDTO: Resultado de una predicción de aprobación.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionDTO:
    """Resultado de una predicción de aprobación.

    Attributes:
        probability: Probabilidad predicha de aprobación (0.0-1.0).
        confidence: Confianza en la predicción (0.0-1.0).
        reasoning_summary: Resumen de los factores que influyeron en la predicción.
    """

    probability: float
    confidence: float
    reasoning_summary: str
