"""
Topics Router — Endpoints para gestión de topics
==================================================
Prefix: /api/v1/topics

Proporciona endpoints CRUD para ResearchTopics:
  - Listar con filtros
  - Obtener por ID
  - Aprobar / Rechazar
  - Crear manual
"""
import dataclasses
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request

from domain.exceptions.base import DomainError
from research.application.dtos import (
    ListTopicsQuery,
    ManualInputDTO,
    ResearchTopicDTO,
    ReviewDecisionDTO,
)
from research.application.use_cases.approve_topic import ApproveTopicUseCase
from research.application.use_cases.list_topics import ListTopicsUseCase
from research.application.use_cases.reject_topic import RejectTopicUseCase
from research.application.use_cases.manual_input import RegisterManualInputUseCase

from presentation.api.container import ApiContainer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


# ── Helpers ──────────────────────────────────────────


async def _get_container(request: Request) -> ApiContainer:
    """Obtiene el container desde app.state."""
    return request.app.state.container


def _topic_to_dict(topic) -> dict:
    """Convierte un ResearchTopic (entity) a dict para JSON."""
    return {
        "id": str(topic.id),
        "title": topic.title,
        "description": topic.description,
        "content_preview": topic.content[:200] if topic.content else "",
        "source_name": topic.source.name,
        "source_type": topic.source.type.value,
        "status": topic.status.value,
        "score_total": (
            topic.score.total
            if hasattr(topic.score, "total")
            else topic.score.relevance
        ),
        "score_components": {
            "relevance": topic.score.relevance,
            "popularity": topic.score.popularity,
            "recency": topic.score.recency,
            "source_reliability": topic.score.source_reliability,
        },
        "url": topic.url,
        "author": topic.author,
        "created_at": (
            topic.created_at.isoformat() if topic.created_at else None
        ),
        "reviewed_at": (
            topic.reviewed_at.isoformat() if topic.reviewed_at else None
        ),
    }


# ── List Topics ──────────────────────────────────────


@router.get("")
async def list_topics(
    request: Request,
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    source: Optional[str] = Query(None, description="Filtrar por nombre de fuente"),
    q: Optional[str] = Query(None, description="Búsqueda textual en título"),
    min_score: Optional[float] = Query(None, description="Score mínimo (0-100)"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
):
    """
    GET /api/v1/topics

    Lista topics con filtros opcionales.

    Query params:
      - status: pending_review, approved, rejected, found
      - source: nombre de fuente (ej: 'Google News')
      - q: búsqueda por texto en título
      - min_score: puntaje mínimo
      - limit: máximo de resultados (default 20, max 100)
    """
    container = await _get_container(request)
    use_case: ListTopicsUseCase = container.list_topics

    query = ListTopicsQuery(
        status=status,
        source=source,
        q=q,
        min_score=min_score,
        limit=limit,
    )
    topic_dtos = await use_case.execute(query)

    # Convertir a dicts para JSON
    topics = [dataclasses.asdict(t) for t in topic_dtos]

    # Filtros adicionales (in-memory) que el repositorio no soporta nativamente
    if source:
        topics = [
            t for t in topics
            if t.get("source_name", "").lower() == source.lower()
        ]
    if q:
        q_lower = q.lower()
        topics = [
            t for t in topics
            if q_lower in t.get("title", "").lower()
            or q_lower in t.get("description", "").lower()
        ]
    if min_score is not None:
        topics = [
            t for t in topics if t.get("score_total", 0) >= min_score
        ]

    return {
        "topics": topics,
        "count": len(topics),
        "filters": {
            "status": status,
            "source": source,
            "q": q,
            "min_score": min_score,
            "limit": limit,
        },
    }


# ── Get Topic ────────────────────────────────────────


@router.get("/{topic_id}")
async def get_topic(
    topic_id: UUID,
    request: Request,
):
    """
    GET /api/v1/topics/{topic_id}

    Obtiene un topic por su UUID.
    """
    container = await _get_container(request)
    topic = await container.research_repository.find_by_id(topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail=f"Topic not found: {topic_id}",
        )
    return _topic_to_dict(topic)


# ── Approve Topic ────────────────────────────────────


@router.post("/{topic_id}/approve")
async def approve_topic(
    topic_id: UUID,
    request: Request,
):
    """
    POST /api/v1/topics/{topic_id}/approve

    Aprueba un topic para generación de contenido.
    """
    container = await _get_container(request)
    use_case: ApproveTopicUseCase = container.approve_topic
    dto = ReviewDecisionDTO(topic_id=topic_id)

    try:
        result = await use_case.execute(dto)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {
        "topic": dataclasses.asdict(result.topic),
        "events": result.events,
    }


# ── Reject Topic ─────────────────────────────────────


@router.post("/{topic_id}/reject")
async def reject_topic(
    topic_id: UUID,
    request: Request,
    reason: str = Query("", description="Motivo de rechazo"),
):
    """
    POST /api/v1/topics/{topic_id}/reject

    Rechaza un topic.
    """
    container = await _get_container(request)
    use_case: RejectTopicUseCase = container.reject_topic
    dto = ReviewDecisionDTO(topic_id=topic_id, reject_reason=reason)

    try:
        result = await use_case.execute(dto)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {
        "topic": dataclasses.asdict(result.topic),
        "events": result.events,
    }


# ── Manual Input ─────────────────────────────────────


@router.post("/manual", status_code=201)
async def create_manual_topic(
    request: Request,
    body: dict,
):
    """
    POST /api/v1/topics/manual

    Crea un topic manualmente.

    Body (JSON):
      - title: str (opcional)
      - url: str (opcional)
      - description: str (opcional)
      - content: str (opcional)
      - author: str (opcional)
      - source_name: str (default "manual")
    """
    container = await _get_container(request)
    use_case: RegisterManualInputUseCase = container.register_manual_input

    dto = ManualInputDTO(
        url=body.get("url"),
        title=body.get("title"),
        content=body.get("content"),
        description=body.get("description"),
        author=body.get("author"),
        source_name=body.get("source_name", "manual"),
    )

    try:
        result = await use_case.execute(dto)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {
        "topic": dataclasses.asdict(result.topic),
        "is_duplicate": result.is_duplicate,
        "events": result.events,
    }
