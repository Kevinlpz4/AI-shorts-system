"""
API Main — FastAPI app factory
================================
Crea y configura la aplicación FastAPI con CORS, routers y error handlers.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from presentation.api.container import ApiContainer
from presentation.api.error_handlers import add_error_handlers
from presentation.api.routes.topics import router as topics_router
from presentation.api.routes.scripts import router as scripts_router
from presentation.api.routes.discover import router as discover_router
from presentation.api.routes.scheduler import router as scheduler_router
from presentation.api.routes.studio import router as studio_router
from presentation.api.routes.script_list import router as script_list_router

logger = logging.getLogger(__name__)


def create_app(container: ApiContainer) -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Args:
        container: ApiContainer con todas las dependencias.

    Returns:
        Instancia de FastAPI configurada.
    """
    app = FastAPI(
        title="AI Shorts System API",
        version=settings.VERSION,
        description="API para gestión de topics y generación de guiones para AI Shorts",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── Almacenar container en app.state ──
    app.state.container = container

    # ── CORS ──
    origins = settings.API_CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("🌐 CORS allowed origins: %s", origins)

    # ── Error handlers ──
    add_error_handlers(app)

    # ── Routers ──
    app.include_router(discover_router)
    app.include_router(scheduler_router)
    app.include_router(scripts_router)
    app.include_router(studio_router)
    app.include_router(script_list_router)
    app.include_router(topics_router)

    # ── Root endpoint ──
    @app.get("/")
    async def root():
        return {
            "service": "AI Shorts System API",
            "version": settings.VERSION,
            "docs": "/api/docs",
        }

    logger.info("✅ FastAPI app created (v%s)", settings.VERSION)
    return app
