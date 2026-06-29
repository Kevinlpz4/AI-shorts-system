"""
Scripts Router — Endpoints para guiones
=========================================
Prefix: /api/v1/topics/{topic_id}/script

Proporciona endpoints para gestionar guiones:
  - Obtener guion existente
  - Generar nuevo guion
  - Regenerar guion existente
"""
import dataclasses
import logging

from fastapi import APIRouter, HTTPException, Request

from application.dtos.script import GenerateScriptRequest, ScriptDTO
from application.use_cases.script.generate_script import GenerateScriptUseCase
from application.use_cases.script.get_script import GetScriptUseCase
from application.use_cases.script.regenerate_script import RegenerateScriptUseCase
from domain.exceptions.base import DomainError
from domain.exceptions.script import ScriptNotFoundError, ScriptAlreadyExistsError
from domain.exceptions.content import ContentError, ScriptValidationError
from research.domain.exceptions import ResearchTopicNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/topics/{topic_id}/script",
    tags=["scripts"],
)


# ── Helpers ──────────────────────────────────────────


async def _get_container(request: Request):
    """Obtiene el container desde app.state."""
    return request.app.state.container


def _script_to_dict(dto: ScriptDTO) -> dict:
    """Convierte ScriptDTO a dict para JSON response."""
    return dataclasses.asdict(dto)


# ── Get Script ───────────────────────────────────────


@router.get("")
async def get_script(
    topic_id: str,
    request: Request,
):
    """
    GET /api/v1/topics/{topic_id}/script

    Obtiene el guion de un topic.

    Returns:
        ScriptResponse si existe.

    Raises:
        404: No se encontró guion para el topic.
    """
    container = await _get_container(request)
    use_case: GetScriptUseCase = container.get_script_use_case

    result = await use_case.execute(topic_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró un guion para el topic {topic_id}",
        )

    return _script_to_dict(result)


# ── Generate Script ──────────────────────────────────


@router.post("/generate", status_code=201)
async def generate_script(
    topic_id: str,
    request: Request,
    body: dict = {},
):
    """
    POST /api/v1/topics/{topic_id}/script/generate

    Genera un nuevo guion para un topic aprobado.

    Body (JSON):
      - duration: int (segundos, default 45)
      - tone: str (default "educational")

    Returns:
        201: Script generado exitosamente.
        404: Topic no encontrado.
        409: Topic no aprobado o ya existe un guion.
        422: Guion generado no pasa validación.
    """
    container = await _get_container(request)
    use_case: GenerateScriptUseCase = container.generate_script_use_case

    dto = GenerateScriptRequest(
        topic_id=topic_id,
        duration=body.get("duration", 45),
        tone=body.get("tone", "educational"),
    )

    try:
        result = await use_case.execute(dto)
    except ResearchTopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)
    except ContentError as e:
        # Topic no aprobado → 409 Conflict
        raise HTTPException(status_code=409, detail=e.detail)
    except ScriptAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.detail)
    except ScriptValidationError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return _script_to_dict(result)


# ── Regenerate Script ────────────────────────────────


@router.post("/regenerate")
async def regenerate_script(
    topic_id: str,
    request: Request,
    body: dict = {},
):
    """
    POST /api/v1/topics/{topic_id}/script/regenerate

    Regenera un guion existente: elimina el anterior y genera uno nuevo.

    Body (JSON):
      - duration: int (segundos, default 45)
      - tone: str (default "educational")

    Returns:
        200: Script regenerado exitosamente.
        404: Topic no encontrado.
        409: Topic no aprobado.
        422: Guion generado no pasa validación.
    """
    container = await _get_container(request)
    use_case: RegenerateScriptUseCase = container.regenerate_script_use_case

    dto = GenerateScriptRequest(
        topic_id=topic_id,
        duration=body.get("duration", 45),
        tone=body.get("tone", "educational"),
    )

    try:
        result = await use_case.execute(dto)
    except ResearchTopicNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.detail)
    except ContentError as e:
        raise HTTPException(status_code=409, detail=e.detail)
    except ScriptValidationError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except DomainError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return _script_to_dict(result)
