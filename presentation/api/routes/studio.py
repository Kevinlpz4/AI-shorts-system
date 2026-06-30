"""
Studio Router — Endpoints para el Script Studio
=================================================
Prefix: /api/v1/studio

Proporciona endpoints para el Studio de generación de guiones:
  - GET /approved-topics → topics aprobados sin script
  - GET /recommendations/{topic_id} → recomendaciones para un topic
"""
import dataclasses
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from research.application.mappers import topic_to_dto
from research.application.recommendations import get_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/studio", tags=["studio"])


# ── Helpers ──────────────────────────────────────────


async def _get_container(request: Request):
    """Obtiene el container desde app.state."""
    return request.app.state.container


# ── Approved Topics Without Script ───────────────────


@router.get("/approved-topics")
async def get_approved_topics_without_script(request: Request) -> dict:
    """
    GET /api/v1/studio/approved-topics

    Retorna los topics aprobados que aún no tienen un script generado.
    Ordenados por score_total DESC (máximo 50).

    Returns:
        topics: list[ResearchTopicDTO]
        count: int
    """
    container = await _get_container(request)
    topics = await container.research_repository.find_approved_without_script()

    # Convertir entidades de dominio a DTOs, luego a dicts
    dtos = [topic_to_dto(t) for t in topics]
    return {
        "topics": [dataclasses.asdict(d) for d in dtos],
        "count": len(dtos),
    }


# ── Recommendations ──────────────────────────────────


@router.get("/recommendations/{topic_id}")
async def get_recommendations_for_topic(
    topic_id: UUID,
    request: Request,
) -> dict:
    """
    GET /api/v1/studio/recommendations/{topic_id}

    Retorna recomendaciones de tono, duración y nicho para un topic.

    Args:
        topic_id: UUID del topic.

    Returns:
        ScriptRecommendations: {tone, duration, niche, reasoning}

    Raises:
        404: Topic no encontrado.
    """
    container = await _get_container(request)
    topic = await container.research_repository.find_by_id(topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail=f"Topic {topic_id} not found",
        )

    recs = get_recommendations(topic)
    return dataclasses.asdict(recs)
