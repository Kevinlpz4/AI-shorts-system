"""
Feedback Queries — consultas para FeedbackRecord.

Queries:
    - GetFeedbackQuery: Obtener un FeedbackRecord por ID.
    - ListFeedbackQuery: Listar FeedbackRecords con filtros y paginación.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetFeedbackQuery:
    """Obtener un FeedbackRecord por su ID.

    Attributes:
        feedback_id: ID del FeedbackRecord a buscar.
    """

    feedback_id: str


@dataclass(frozen=True)
class ListFeedbackQuery:
    """Listar FeedbackRecords con filtros opcionales y paginación.

    Attributes:
        topic_id: Filtrar por topic_id (opcional).
        source_name: Filtrar por source_name (opcional).
        page: Página actual (1-indexed, default: 1).
        size: Tamaño de página (default: 50).
    """

    topic_id: str | None = None
    source_name: str | None = None
    page: int = 1
    size: int = 50
