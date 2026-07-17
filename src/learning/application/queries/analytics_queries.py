"""
Analytics Queries — consultas de analíticas del BC Learning.

Queries:
    - GetAnalyticsQuery: Obtener analíticas generales del sistema de aprendizaje.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetAnalyticsQuery:
    """Obtener analíticas generales del sistema de aprendizaje.

    Attributes:
        time_window_start: Inicio de la ventana de tiempo (ISO format, opcional).
        time_window_end: Fin de la ventana de tiempo (ISO format, opcional).
    """

    time_window_start: str | None = None
    time_window_end: str | None = None
