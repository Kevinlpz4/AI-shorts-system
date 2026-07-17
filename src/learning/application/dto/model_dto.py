"""
Model DTO — representación de datos de LearningModel.

DTOs:
    - LearningModelDTO: Vista completa del modelo de aprendizaje.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningModelDTO:
    """Representación del modelo de aprendizaje actual.

    Attributes:
        id: ID único del modelo.
        algorithm_version: Versión del algoritmo (ej: "1.2.3").
        weights: Pesos de scoring actuales (relevance, popularity, recency, source_reliability).
        minimum_confidence: Umbral mínimo de confianza (0.0-1.0).
        minimum_sample_size: Tamaño mínimo de muestra para señales válidas (>= 1).
        rules_count: Número de reglas activas.
    """

    id: str
    algorithm_version: str
    weights: dict[str, float]
    minimum_confidence: float
    minimum_sample_size: int
    rules_count: int
