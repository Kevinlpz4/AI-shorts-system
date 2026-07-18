"""
FastAPI application factory for the Learning Intelligence API.

Creates and configures the FastAPI app with middleware, routers,
and OpenAPI customization. Follows the factory pattern — no global state.
"""
from __future__ import annotations

from fastapi import FastAPI

from learning.presentation.health.router import router as health_router
from learning.presentation.middleware.request_id import RequestIdMiddleware
from learning.presentation.middleware.timing import TimingMiddleware
from learning.presentation.routers import (
    analytics,
    artifacts,
    datasets,
    explanation,
    feedback,
    knowledge,
    prediction,
    recommendation,
    signals,
    source_intelligence,
    timeline,
)
from learning.presentation.openapi.customization import customize_openapi


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance with all routers, middleware,
        and OpenAPI customization applied.
    """
    app = FastAPI(
        title="Learning Intelligence API",
        description="API for querying accumulated knowledge from the Learning BC",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware (applied in reverse order — last added = first executed)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Health endpoints (no prefix)
    app.include_router(health_router)

    # API routers with prefix and tags
    api_prefix = "/api/v1/learning"
    app.include_router(prediction.router, prefix=api_prefix, tags=["Prediction"])
    app.include_router(explanation.router, prefix=api_prefix, tags=["Explanation"])
    app.include_router(recommendation.router, prefix=api_prefix, tags=["Recommendation"])
    app.include_router(feedback.router, prefix=api_prefix, tags=["Feedback"])
    app.include_router(
        source_intelligence.router, prefix=api_prefix, tags=["Source Intelligence"]
    )
    app.include_router(knowledge.router, prefix=api_prefix, tags=["Knowledge"])
    app.include_router(timeline.router, prefix=api_prefix, tags=["Timeline"])
    app.include_router(signals.router, prefix=api_prefix, tags=["Signals"])
    app.include_router(datasets.router, prefix=api_prefix, tags=["Datasets"])
    app.include_router(artifacts.router, prefix=api_prefix, tags=["Artifacts"])
    app.include_router(analytics.router, prefix=api_prefix, tags=["Analytics"])

    # OpenAPI customization
    custom = customize_openapi()
    app.openapi_tags = custom.get("tags", [])

    return app


# Module-level app instance for uvicorn
app = create_app()
