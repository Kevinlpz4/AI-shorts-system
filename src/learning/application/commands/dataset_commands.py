"""
Dataset Commands — operaciones de generación de datasets de entrenamiento.

Commands:
    - GenerateDatasetCommand: Generar un dataset de entrenamiento para ML.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateDatasetCommand:
    """Generar un dataset de entrenamiento para ML.

    Attributes:
        name: Nombre descriptivo del dataset.
        time_window_start: Inicio de la ventana de tiempo (ISO format).
        time_window_end: Fin de la ventana de tiempo (ISO format).
        max_samples: Número máximo de muestras (opcional).
    """

    name: str
    time_window_start: str
    time_window_end: str
    max_samples: int | None = None
