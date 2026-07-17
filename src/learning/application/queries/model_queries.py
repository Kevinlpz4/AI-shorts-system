"""
Model Queries — consultas para LearningModel, SourceQualityProfile y LearningSignal.

Queries:
    - GetLearningModelQuery: Obtener el modelo de aprendizaje actual.
    - GetSourceQualityQuery: Obtener el perfil de calidad de una fuente.
    - GetLearningSignalsQuery: Obtener señales de aprendizaje con filtros.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetLearningModelQuery:
    """Obtener el modelo de aprendizaje actual.

    Sin atributos — el modelo es singleton en el dominio.
    """


@dataclass(frozen=True)
class GetSourceQualityQuery:
    """Obtener el perfil de calidad de una fuente específica.

    Attributes:
        source_name: Nombre de la fuente a consultar.
    """

    source_name: str


@dataclass(frozen=True)
class GetLearningSignalsQuery:
    """Obtener señales de aprendizaje con filtros opcionales.

    Attributes:
        dimension: Filtrar por dimensión (KEYWORD, SOURCE, etc.) (opcional).
        source: Filtrar por valor específico (opcional).
    """

    dimension: str | None = None
    source: str | None = None
