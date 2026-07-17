"""
Dataset DTO — representación de datasets de entrenamiento.

DTOs:
    - DatasetDTO: Información de un dataset de entrenamiento.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetDTO:
    """Representación de un dataset de entrenamiento.

    Attributes:
        id: ID único del dataset.
        name: Nombre descriptivo del dataset.
        time_window_start: Inicio de la ventana de tiempo (ISO format).
        time_window_end: Fin de la ventana de tiempo (ISO format).
        sample_count: Número de muestras en el dataset.
        created_at: Timestamp de creación (ISO format).
    """

    id: str
    name: str
    time_window_start: str
    time_window_end: str
    sample_count: int
    created_at: str
