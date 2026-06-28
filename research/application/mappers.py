"""
Mappers — Conversión entre entidades de dominio y DTOs
=========================================================
Funciones PURAS que convierten de un formato a otro.
Sin lógica de negocio, sin efectos secundarios.

Separar los mappers de los use cases:
  - DRY: los mappers se comparten entre todos los use cases
  - SRP: los use cases orquestan, los mappers convierten
  - Testeable: se pueden testear los mappers independientemente
"""

from datetime import datetime
from typing import Any

from uuid import UUID

from research.application.dtos import ResearchTopicDTO
from research.domain.entities.research_topic import ResearchTopic


def topic_to_dto(topic: ResearchTopic) -> ResearchTopicDTO:
    """
    Convierte una entidad ResearchTopic → ResearchTopicDTO.

    Es una función pura: mismo input → mismo output.
    No modifica la entidad.
    """
    return ResearchTopicDTO(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        content_preview=topic.content[:200] if topic.content else "",
        source_name=topic.source.name,
        source_type=topic.source.type.value,
        status=topic.status.value,
        score_total=topic.score.total,
        score_components=topic.score.to_dict() if hasattr(topic.score, 'to_dict') else {
            "relevance": topic.score.relevance,
            "popularity": topic.score.popularity,
            "recency": topic.score.recency,
            "source_reliability": topic.score.source_reliability,
        },
        url=topic.url,
        author=topic.author,
        created_at=topic.created_at,
        reviewed_at=topic.reviewed_at,
    )


def event_to_dict(event: Any) -> dict:
    """
    Convierte un evento de dominio a dict plano.

    Maneja:
      - UUID → str
      - datetime → str ISO
      - Cualquier otro objeto → str
      - Atributos privados (_events, etc.) se excluyen
    """
    def _serialize(v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, UUID):
            return str(v)
        return v

    return {
        "type": event.__class__.__name__,
        "data": {
            k: _serialize(v)
            for k, v in event.__dict__.items()
            if not k.startswith("_")
        },
    }
