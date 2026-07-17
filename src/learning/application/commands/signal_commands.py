"""
Signal Commands — operaciones de registro de señales de aprendizaje.

Commands:
    - RegisterSignalCommand: Registrar una nueva señal de aprendizaje.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterSignalCommand:
    """Registrar una nueva señal de aprendizaje.

    Attributes:
        dimension: Dimensión de la señal (KEYWORD, SOURCE, etc.).
        source: Valor específico dentro de la dimensión (ej: nombre de keyword).
        value: Valor de la señal (0.0-1.0).
    """

    dimension: str
    source: str
    value: float
