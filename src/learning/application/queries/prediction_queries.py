"""
Prediction Queries — consultas de predicción y explicabilidad.

Queries:
    - PredictApprovalQuery: Predecir probabilidad de aprobación para una fuente.
    - ExplainScoreQuery: Explicar el score de una fuente con features específicas.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictApprovalQuery:
    """Predecir probabilidad de aprobación para contenido de una fuente.

    Attributes:
        source_name: Nombre de la fuente.
        features: Features de scoring específicas (opcional).
    """

    source_name: str
    features: dict[str, float] | None = None


@dataclass(frozen=True)
class ExplainScoreQuery:
    """Explicar el score de una fuente con features específicas.

    Attributes:
        source_name: Nombre de la fuente.
        features: Features de scoring específicas (opcional).
    """

    source_name: str
    features: dict[str, float] | None = None
