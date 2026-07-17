"""
Feedback DTOs — representaciones de datos de FeedbackRecord.

DTOs:
    - FeedbackSummaryDTO: Vista resumida (sin relaciones).
    - FeedbackDetailDTO: Vista completa con razón y features.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackSummaryDTO:
    """Resumen de un FeedbackRecord.

    Attributes:
        id: ID único del feedback.
        topic_id: ID del topic (referencia a Ingestion).
        decision: Tipo de decisión (APPROVED, REJECTED, etc.).
        source_name: Nombre de la fuente de contenido.
        created_at: Timestamp de creación (ISO format).
    """

    id: str
    topic_id: str
    decision: str
    source_name: str
    created_at: str


@dataclass(frozen=True)
class FeedbackDetailDTO:
    """Detalle completo de un FeedbackRecord.

    Attributes:
        id: ID único del feedback.
        topic_id: ID del topic (referencia a Ingestion).
        decision: Tipo de decisión (APPROVED, REJECTED, etc.).
        reason: Razón de la decisión (requerida para rechazos).
        source_name: Nombre de la fuente de contenido.
        title: Título del contenido decidido.
        features: Snapshot de features de scoring al momento de la decisión.
        created_at: Timestamp de creación (ISO format).
    """

    id: str
    topic_id: str
    decision: str
    reason: str | None
    source_name: str
    title: str
    features: dict[str, float] | None
    created_at: str
