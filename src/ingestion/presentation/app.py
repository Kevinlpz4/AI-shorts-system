"""
FastAPI Application Factory.

Creates a fully configured FastAPI instance with:
- Middleware stack (SecurityHeaders → TrustedHost → Recovery → Timing → CorrelationID → RequestID)
- Exception handlers (FoundationError hierarchy → Problem Details)
- Health endpoints (/health/live, /health/ready)
- CORS configuration
- SECRET_KEY validation (startup fail-fast in production)
- Lifespan management (engine creation/disposal)

Usage::

    from ingestion.presentation.app import create_app
    app = create_app()       # default Settings from env
    app = create_app(settings=my_settings)  # custom Settings
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from ingestion.presentation.config import Settings
from ingestion.presentation.exceptions import register_exception_handlers
from ingestion.presentation.health import router as health_router
from ingestion.presentation.routers.sources import router as sources_router
from ingestion.presentation.routers.feeds import router as feeds_router
from ingestion.presentation.routers.articles import router as articles_router
from ingestion.presentation.routers.categories import router as categories_router
from ingestion.presentation.routers.topics import router as topics_router
from ingestion.presentation.logging_config import setup_logging
from ingestion.presentation.middleware import (
    CorrelationIDMiddleware,
    RecoveryMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
    TrustedHostMiddleware,
)

logger = logging.getLogger(__name__)

_INSECURE_SECRET_KEYS = frozenset({
    "change-me-in-production",
    "change-me",
    "changeme",
    "secret",
    "password",
    "",
})


def _validate_startup_settings(settings: Settings) -> None:
    """Validate settings at startup. Raises RuntimeError on critical failures.

    This runs AFTER Settings is constructed (pydantic validation passed),
    but checks environment-specific rules that require knowing the ENVIRONMENT.
    """
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY.strip().lower() in _INSECURE_SECRET_KEYS:
            raise RuntimeError(
                "CRITICAL: SECRET_KEY must be changed from its default value in production. "
                "Generate a secure key: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if settings.DEBUG:
            logger.warning(
                "DEBUG mode is enabled in production — this may expose sensitive information"
            )
        if settings.CORS_ORIGINS == ["http://localhost:3000"]:
            logger.warning(
                "CORS_ORIGINS is set to localhost default in production — "
                "configure AI_SHORTS_CORS_ORIGINS for your domain"
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
        SecurityHeaders → TrustedHost → Recovery → Timing → CorrelationID → RequestID → Handler

    Args:
        settings: Optional Settings instance. If None, creates from env.

    Returns:
        Fully configured FastAPI application.

    Raises:
        RuntimeError: If production settings are invalid (e.g., insecure SECRET_KEY).
    """
    if settings is None:
        settings = Settings()

    # Startup validation — fail-fast for production
    _validate_startup_settings(settings)

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

    # ── Middleware (order: last added = first executed = outermost) ──
    # NOTE: add_middleware() uses insert(0, ...) so the LAST call = OUTERMOST.
    # We add innermost first, outermost last.
    #
    # Desired execution order (outermost first):
    #   CORS → SecurityHeaders → TrustedHost → Recovery → Timing → RequestID → CorrelationID → Handler
    #
    # RequestID MUST be outermost among custom middleware because
    # CorrelationIDMiddleware reads request.state.request_id as fallback.
    #
    app.add_middleware(CorrelationIDMiddleware)     # innermost (last to execute on request)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RecoveryMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    app.add_middleware(
        SecurityHeadersMiddleware,
        enabled=settings.SECURITY_HEADERS_ENABLED,
    )

    # ── Exception handlers ──
    register_exception_handlers(app)

    # ── Health endpoints (outside /api/v1) ──
    app.include_router(health_router)

    # ── API v1 endpoints ──
    app.include_router(sources_router, prefix="/api/v1")
    app.include_router(feeds_router, prefix="/api/v1")
    app.include_router(articles_router, prefix="/api/v1")
    app.include_router(categories_router, prefix="/api/v1")
    app.include_router(topics_router, prefix="/api/v1")

    # ── CORS (outermost in production, after security headers) ──
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
