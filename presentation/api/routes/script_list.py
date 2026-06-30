"""
Script List Router — Endpoint para listar scripts generados
=============================================================
Prefix: /api/v1/scripts

Proporciona el endpoint para obtener todos los scripts generados
con información del topic asociado (título, score, status).

Esta página es la base para la conversión a voz (TTS).
"""
import dataclasses
import logging
from uuid import UUID

from fastapi import APIRouter, Request

from application.dtos.script import ScriptDTO

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/scripts",
    tags=["scripts"],
)


async def _get_container(request: Request):
    return request.app.state.container


@router.get("")
async def list_scripts(
    request: Request,
    limit: int = 50,
    offset: int = 0,
):
    """
    GET /api/v1/scripts

    Lista todos los scripts generados, ordenados por fecha descendente,
    con información del topic asociado (título, score_total, status).

    Args:
        limit: Máximo de resultados (default 50).
        offset: Paginación (default 0).

    Returns:
        Dict con scripts y count total.
    """
    container = await _get_container(request)
    script_repo = container.script_repo
    topic_repo = container.research_repository

    scripts = await script_repo.find_all(limit=limit, offset=offset)
    total = await script_repo.count_all()

    items = []
    for script in scripts:
        dto = ScriptDTO.from_entity(script)
        item = dataclasses.asdict(dto)

        # Enriquecer con datos del topic
        try:
            topic = await topic_repo.find_by_id(UUID(script.topic_id))
            if topic:
                item["topic_title"] = topic.title
                item["topic_score"] = topic.score.total
                item["topic_status"] = topic.status.value
            else:
                item["topic_title"] = "Unknown Topic"
                item["topic_score"] = 0
                item["topic_status"] = "unknown"
        except Exception:
            item["topic_title"] = "Unknown Topic"
            item["topic_score"] = 0
            item["topic_status"] = "unknown"

        items.append(item)

    return {
        "scripts": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
