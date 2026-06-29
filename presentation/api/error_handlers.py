"""
Error Handlers — Manejadores de errores para FastAPI
======================================================
Registra exception handlers que convierten DomainError → respuesta JSON
usando el ErrorMapper.

Provee consistencia en todas las respuestas de error de la API.
"""
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions.base import DomainError
from application.error_mapper import ErrorMapper

logger = logging.getLogger(__name__)


def add_error_handlers(app: FastAPI) -> None:
    """
    Registra todos los exception handlers en la aplicación FastAPI.

    Args:
        app: Instancia de FastAPI a configurar.
    """
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_exception_handler(Exception, _generic_error_handler)
    logger.debug("✅ Error handlers registrados")


async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """
    Maneja DomainError → respuesta JSON estructurada.

    Extrae request_id del estado de la request si está disponible.
    """
    response_data = ErrorMapper.to_response(exc)
    status_code = response_data["status_code"]

    # Agregar request_id si está disponible en el scope
    request_id = _get_request_id(request)
    if request_id:
        response_data["request_id"] = request_id

    logger.log(
        logging.getLevelName(response_data.get("level", "ERROR")),
        "DomainError [%s]: %s | path=%s",
        exc.code,
        exc.detail,
        request.url.path,
    )

    return JSONResponse(
        status_code=status_code,
        content=response_data,
    )


async def _generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Maneja excepciones no controladas → 500 JSON.

    Nunca expone el traceback al cliente en producción.
    """
    logger.exception(
        "Unhandled exception [%s]: %s | path=%s",
        type(exc).__name__,
        str(exc),
        request.url.path,
    )

    response_data: dict = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "Error interno del servidor",
        "detail": str(exc) if _is_debug_mode(request) else None,
        "status_code": 500,
        "level": "ERROR",
    }

    request_id = _get_request_id(request)
    if request_id:
        response_data["request_id"] = request_id

    return JSONResponse(
        status_code=500,
        content=response_data,
    )


def _get_request_id(request: Request) -> Optional[str]:
    """Extrae request_id del scope de la request si existe."""
    return request.scope.get("request_id")


def _is_debug_mode(request: Request) -> bool:
    """Determina si el detalle del error debe exponerse."""
    return request.app.debug
