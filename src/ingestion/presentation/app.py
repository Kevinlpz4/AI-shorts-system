"""
FastAPI Application Factory.

Creates a fully configured FastAPI instance with:
- Middleware stack (Recovery → Timing → CorrelationID → RequestID)
- Exception handlers (FoundationError hierarchy → Problem Details)
- Health endpoints (/health/live, /health/ready)
- CORS configuration
- Lifespan management (engine creation/disposal)

Usage::

    from ingestion.presentation.app import create_app
    app = create_app()       # default Settings from env
    app = create_app(settings=my_settings)  # custom Settings
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from ingestion.presentation.config import Settings
from ingestion.presentation.exceptions import register_exception_handlers
from ingestion.presentation.health import router as health_router
from ingestion.presentation.routers.sources import router as sources_router
from ingestion.presentation.routers.feeds import router as feeds_router
from ingestion.presentation.logging_config import setup_logging
from ingestion.presentation.middleware import (
    CorrelationIDMiddleware,
    RecoveryMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
)


@asynccontextmanager
async def _create_lifespan(settings: Settings) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Creates engine and session_factory during startup,
    stores them on ``app.state``, and disposes on shutdown.

    Note:
        Engine and session_factory are created here but stored on
        app.state by the ``create_app()`` function after the lifespan
        is set up. The actual creation happens in create_app for
        testability.
    """
    # Startup: nothing extra needed here (engine created in create_app)
    yield
    # Shutdown: engine disposal handled by create_app


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Creates a configured FastAPI instance.

    Middleware order (last added = first executed):
        Recovery → Timing → CorrelationID → RequestID → Handler

    Args:
        settings: Optional Settings instance. If None, creates from env.

    Returns:
        Fully configured FastAPI application.
    """
    if settings is None:
        settings = Settings()

    # Setup structured logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
    )

    # Create engine and session factory
    from sqlalchemy import create_engine as sa_create_engine
    from sqlalchemy.orm import sessionmaker

    engine = sa_create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
    sf = sessionmaker(bind=engine, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Store on app.state for DI access
        app.state.settings = settings
        app.state.engine = engine
        app.state.session_factory = sf
        yield
        # Shutdown
        engine.dispose()

    app = FastAPI(
        title=f"AI Shorts System — Ingestion API v{settings.openapi_version}",
        description="News ingestion bounded context API",
        version=settings.openapi_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    # Store settings on app.state (also set in lifespan for immediate access)
    app.state.settings = settings

    # ── Middleware (order: last added = first executed) ──
    app.add_middleware(RecoveryMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Exception handlers ──
    register_exception_handlers(app)

    # ── Health endpoints (outside /api/v1) ──
    app.include_router(health_router)

    # ── API v1 endpoints ──
    app.include_router(sources_router, prefix="/api/v1")
    app.include_router(feeds_router, prefix="/api/v1")

    # ── CORS ──
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
