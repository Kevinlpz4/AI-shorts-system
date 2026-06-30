"""
Scheduler Router — Endpoints para control del scheduler de descubrimiento
==========================================================================
Prefix: /api/v1/scheduler

Proporciona endpoints para gestionar el ResearchScheduler:
  - GET /status → estado actual del scheduler
  - POST /start → iniciar scheduler
  - POST /stop → detener scheduler
  - POST /run-now → ejecutar un ciclo inmediato
  - GET /config → obtener configuración
  - PUT /config → actualizar configuración
"""
import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


# ── Helpers ──────────────────────────────────────────


async def _get_container(request: Request):
    """Obtiene el container desde app.state."""
    return request.app.state.container


# ── Status ───────────────────────────────────────────


@router.get("/status")
async def get_scheduler_status(request: Request) -> dict:
    """
    GET /api/v1/scheduler/status

    Retorna el estado actual del scheduler: enabled, interval, queries,
    last_run, is_running, running_query.

    Returns:
        Status completo del scheduler (siempre 200).
    """
    container = await _get_container(request)
    return container.research_scheduler.get_status()


# ── Start / Stop ─────────────────────────────────────


@router.post("/start")
async def start_scheduler(request: Request) -> dict:
    """
    POST /api/v1/scheduler/start

    Inicia el scheduler de descubrimiento automático.
    Si ya está corriendo, es idempotente.

    Returns:
        {"status": "started"}
    """
    container = await _get_container(request)
    await container.research_scheduler.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_scheduler(request: Request) -> dict:
    """
    POST /api/v1/scheduler/stop

    Detiene el scheduler gracefulmente.
    Si ya está detenido, es idempotente.

    Returns:
        {"status": "stopped"}
    """
    container = await _get_container(request)
    await container.research_scheduler.stop()
    return {"status": "stopped"}


@router.post("/run-now")
async def run_scheduler_now(request: Request) -> dict:
    """
    POST /api/v1/scheduler/run-now

    Ejecuta un ciclo de descubrimiento inmediatamente (sin esperar
    el intervalo configurado).

    Returns:
        Dict con discovered_count, duplicates_count, errors del ciclo.
    """
    container = await _get_container(request)
    result = await container.research_scheduler.run_once()
    return result


# ── Config ───────────────────────────────────────────


@router.get("/config")
async def get_scheduler_config(request: Request) -> dict:
    """
    GET /api/v1/scheduler/config

    Retorna la configuración actual del scheduler.

    Returns:
        Config con interval_minutes, queries, auto_generate_script.
    """
    container = await _get_container(request)
    cfg = container.scheduler_config
    return {
        "interval_minutes": cfg.get_interval(),
        "queries": cfg.get_queries(),
        "auto_generate_script": cfg.is_auto_generate_enabled(),
    }


@router.put("/config")
async def update_scheduler_config(request: Request, body: dict) -> dict:
    """
    PUT /api/v1/scheduler/config

    Actualiza la configuración del scheduler.
    Solo actualiza los campos presentes en el body.

    Body (JSON):
        - interval_minutes: int (opcional)
        - queries: list[str] (opcional)
        - auto_generate_script: bool (opcional)

    Returns:
        Config actualizada con interval_minutes, queries, auto_generate_script.
    """
    container = await _get_container(request)
    cfg = container.scheduler_config

    if "interval_minutes" in body:
        cfg.set_interval(body["interval_minutes"])
    if "queries" in body:
        cfg.set_queries(body["queries"])
    if "auto_generate_script" in body:
        cfg.set_auto_generate(body["auto_generate_script"])

    return {
        "interval_minutes": cfg.get_interval(),
        "queries": cfg.get_queries(),
        "auto_generate_script": cfg.is_auto_generate_enabled(),
    }
