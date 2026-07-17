"""
Recommendation DTO — representación de recomendaciones de contenido.

DTOs:
    - RecommendationDTO: Recomendación generada para contenido nuevo.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationDTO:
    """Recomendación generada para contenido nuevo.

    Attributes:
        recommendation: Tipo de recomendación ("APPROVE", "REJECT", "MANUAL_REVIEW").
        probability: Probabilidad predicha de aprobación (0.0-1.0).
        confidence: Confianza en la predicción (0.0-1.0).
        reasoning: Lista de razones que respaldan la recomendación.
        source_quality: Tasa de aprobación acumulada de la fuente (0.0-1.0).
        model_version: Versión del algoritmo utilizado.
    """

    recommendation: str  # "APPROVE", "REJECT", "MANUAL_REVIEW"
    probability: float
    confidence: float
    reasoning: tuple[str, ...]  # List of reasons
    source_quality: float
    model_version: str
