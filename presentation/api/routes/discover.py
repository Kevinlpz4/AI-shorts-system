"""
Discover Router — Endpoints para descubrimiento y estado del sistema
=====================================================================
Prefix: /api/v1

Proporciona:
  - POST /api/v1/discover → descubrimiento automático de topics
  - GET /api/v1/status → estado del sistema
"""
import dataclasses
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from application.use_cases.script.get_script import GetScriptUseCase
from domain.exceptions.base import DomainError
from research.application.dtos import AutoDiscoverDTO
from research.application.use_cases.auto_discover import AutoDiscoverTopicsUseCase
from research.domain.value_objects.research_status import ResearchStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["discover"])

# ── Uptime tracking ─────────────────────────────────
_start_time: float = time.time()


# ── Helpers ──────────────────────────────────────────


async def _get_container(request: Request):
    """Obtiene el container desde app.state."""
    return request.app.state.container


# ── Discover Topics ──────────────────────────────────


@router.post("/discover")
async def discover_topics(
    request: Request,
    body: Optional[dict] = None,
):
    """
    POST /api/v1/discover

    Dispara descubrimiento automático de topics desde fuentes externas.

    Body (JSON, opcional):
      - query: str (término de búsqueda)
      - limit: int (resultados por fuente, default 5)
      - source_names: list[str] (fuentes específicas, default todas)

    Returns:
        Topics descubiertos, duplicados y errores por fuente.
    """
    container = await _get_container(request)
    use_case: AutoDiscoverTopicsUseCase = container.auto_discover_topics

    data = body or {}
    dto = AutoDiscoverDTO(
        query=data.get("query"),
        limit=data.get("limit", 5),
        source_names=data.get("source_names"),
    )

    try:
        result = await use_case.execute(dto)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    discovered = [dataclasses.asdict(t) for t in result.discovered]
    duplicates = [dataclasses.asdict(t) for t in result.duplicates]

    return {
        "discovered": discovered,
        "duplicates": duplicates,
        "errors": result.errors,
        "count": len(discovered),
    }


# ── System Status ────────────────────────────────────


@router.get("/status")
async def system_status(
    request: Request,
):
    """
    GET /api/v1/status

    Estado del sistema: conteo de topics, versión, uptime.

    Returns:
        Status del backend con métricas generales.
    """
    from app.config import settings

    container = await _get_container(request)
    list_uc = container.list_topics

    # Obtener conteos por estado
    counts = {}
    for s in ResearchStatus:
        try:
            count = await container.research_repository.count_by_status(s)
            counts[s.value] = count
        except Exception:
            counts[s.value] = -1

    uptime_seconds = int(time.time() - _start_time)

    return {
        "version": settings.VERSION,
        "uptime_seconds": uptime_seconds,
        "topics": counts,
        "total_topics": sum(v for v in counts.values() if v >= 0),
        "api_version": "1.0.0",
    }
