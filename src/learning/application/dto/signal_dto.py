"""
Signal DTO — representación de datos de LearningSignal.

DTOs:
    - LearningSignalDTO: Vista completa de una señal de aprendizaje.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningSignalDTO:
    """Representación de una señal de aprendizaje.

    Attributes:
        id: ID único de la señal.
        dimension: Dimensión de la señal (KEYWORD, SOURCE, etc.).
        source: Valor específico dentro de la dimensión.
        sample_size: Número de registros contribuyentes.
        approval_rate: Tasa de aprobación (0.0-1.0).
        strength: Fuerza de la señal (0.0-1.0).
        decay_factor: Factor de decaimiento temporal (0.0-1.0).
        updated_at: Timestamp de última actualización (ISO format).
    """

    id: str
    dimension: str
    source: str
    sample_size: int
    approval_rate: float
    strength: float
    decay_factor: float
    updated_at: str
