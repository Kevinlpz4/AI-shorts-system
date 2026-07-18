"""
Health check endpoints — /health, /ready, /live.

Kubernetes-compatible health probes for the Learning Intelligence API.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Check if the service is healthy and operational.

    Returns a simple status object confirming the service is running.
    """
    return {"status": "healthy", "service": "learning-intelligence-api"}


@router.get("/ready", summary="Readiness check")
async def ready() -> dict[str, str]:
    """Check if the service is ready to accept traffic.

    Use this probe to determine when the service has finished
    initialization and can handle requests.
    """
    return {"status": "ready", "service": "learning-intelligence-api"}


@router.get("/live", summary="Liveness check")
async def live() -> dict[str, str]:
    """Check if the service process is alive.

    Use this probe to detect deadlocks or unresponsive processes.
    """
    return {"status": "alive", "service": "learning-intelligence-api"}
