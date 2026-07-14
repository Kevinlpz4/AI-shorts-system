"""
Health Check Endpoints.

Provides liveness and readiness probes OUTSIDE ``/api/v1``:

- ``GET /health/live`` → Always 200 ``{"status": "alive"}``
- ``GET /health/ready`` → 200 ``{"status": "ready"}`` or 503 ``{"status": "not_ready"}``

Usage::

    from ingestion.presentation.health import health_router
    app.include_router(health_router)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from starlette.responses import JSONResponse

from ingestion.presentation.dependencies import get_session_factory

router = APIRouter(tags=["System"])


@router.get("/health/live", response_model=None)
async def liveness() -> dict[str, str]:
    """Liveness probe — always returns alive.

    Indicates the process is running and accepting requests.
    """
    return {"status": "alive"}


@router.get("/health/ready", response_model=None)
async def readiness(
    session_factory: sessionmaker = Depends(get_session_factory),
) -> dict[str, str] | JSONResponse:
    """Readiness probe — checks DB connectivity.

    Executes ``SELECT 1`` to verify the database is reachable.
    Returns 503 if the check fails.

    Args:
        session_factory: SQLAlchemy sessionmaker (injected via DI from app.state).
    """
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"},
        )
