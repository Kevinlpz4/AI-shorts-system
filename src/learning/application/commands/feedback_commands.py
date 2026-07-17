"""
Feedback Commands — operaciones de grabación y archivo para FeedbackRecord.

Commands:
    - RecordFeedbackCommand: Grabar una decisión humana sobre contenido.
    - ArchiveFeedbackCommand: Archivar un FeedbackRecord existente.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordFeedbackCommand:
    """Grabar una decisión humana sobre contenido.

    Attributes:
        topic_id: ID del topic (referencia a Ingestion).
        decision: Tipo de decisión (APPROVED, REJECTED, etc.).
        reason: Razón de la decisión (requerida para rechazos).
        source_name: Nombre de la fuente de contenido.
        title: Título del contenido decidido.
        features: Snapshot de features de scoring al momento de la decisión.
    """

    topic_id: str
    decision: str
    reason: str | None
    source_name: str
    title: str
    features: dict[str, float] | None = None


@dataclass(frozen=True)
class ArchiveFeedbackCommand:
    """Archivar un FeedbackRecord existente.

    Attributes:
        feedback_id: ID del FeedbackRecord a archivar.
    """

    feedback_id: str
