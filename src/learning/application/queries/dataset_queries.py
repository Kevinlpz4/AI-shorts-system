"""
Dataset Queries — consultas para datasets de entrenamiento.

Queries:
    - ListDatasetsQuery: Listar datasets de entrenamiento con paginación.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListDatasetsQuery:
    """Listar datasets de entrenamiento con paginación.

    Attributes:
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    page: int = 1
    size: int = 50
