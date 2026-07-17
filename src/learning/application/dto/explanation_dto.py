"""
Explanation DTO — representación de explicaciones de scoring.

DTOs:
    - ExplanationDTO: Explicación detallada del score de una fuente.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplanationDTO:
    """Explicación detallada del score de una fuente.

    Attributes:
        source_name: Nombre de la fuente.
        base_score: Score base de contenido (0.0-1.0).
        freshness_score: Score de frescura temporal (0.0-1.0).
        keyword_bonus: Bonus por coincidencia de keywords (0.0-1.0).
        source_bonus: Bonus por confiabilidad de la fuente (0.0-1.0).
        topic_penalty: Penalización por mismatch de topic (0.0-1.0).
        confidence: Confianza en el scoring (0.0-1.0).
        final_score: Score final calculado (0.0-1.0).
        timestamp: Timestamp del scoring (ISO format).
        model_version: Versión del algoritmo que produjo el score.
        active_signals: Señales activas que influyeron en el score.
    """

    source_name: str
    base_score: float
    freshness_score: float
    keyword_bonus: float
    source_bonus: float
    topic_penalty: float
    confidence: float
    final_score: float
    timestamp: str
    model_version: str
    active_signals: tuple[str, ...]
