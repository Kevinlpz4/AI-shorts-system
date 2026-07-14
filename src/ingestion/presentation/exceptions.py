"""
Problem Details (RFC 9457) + Exception Handlers + Error Mappers.

All error responses in the Presentation Layer are RFC 9457 Problem Details
JSON objects with ``Content-Type: application/problem+json``.

Error flow:
    1. Application Services return ``Result[T]`` (never raise).
    2. Router handlers map ``Error.code`` → HTTP status via mapper dicts.
    3. Infrastructure exceptions (PersistenceError, FoundationError) are
       caught by global exception handlers.

Usage::

    from ingestion.presentation.exceptions import problem_response

    return problem_response(
        status=404,
        type_uri="https://api.ai-shorts.dev/errors/not-found",
        title="Not Found",
        detail="Source 'abc' not found",
    )
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse

from foundation.errors import (
    FoundationError,
    InfrastructureError,
)
from ingestion.infrastructure.persistence.exceptions import (
    PersistenceError,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Problem Detail Model
# ══════════════════════════════════════════════════════════════════════════════


class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs.

    Attributes:
        type: URI reference identifying the problem type.
        title: Short human-readable summary.
        status: HTTP status code.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI reference identifying the specific occurrence.
        error_code: Custom extension for machine-readable error code.
    """

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    error_code: str | None = None


def problem_response(
    status: int,
    type_uri: str,
    title: str,
    detail: str,
    instance: str | None = None,
    error_code: str | None = None,
) -> JSONResponse:
    """Create an RFC 9457 Problem Details JSON response.

    Args:
        status: HTTP status code.
        type_uri: URI identifying the problem type.
        title: Short human-readable summary.
        detail: Human-readable explanation.
        instance: URI identifying the specific occurrence.
        error_code: Custom extension for machine-readable error code.

    Returns:
        JSONResponse with Content-Type ``application/problem+json``.
    """
    body = ProblemDetail(
        type=type_uri,
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        error_code=error_code,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Error Code → HTTP Status Mappers
# ══════════════════════════════════════════════════════════════════════════════

# ── Application Error Codes (from ErrorMapper) → HTTP Status ──
_APP_CODE_TO_STATUS: dict[str, int] = {
    "COMMAND_INVALID": 422,
    "COMMAND_MISSING_FIELD": 422,
    "RESOURCE_NOT_FOUND": 404,
    "OPERATION_FAILED": 500,
    "TRANSACTION_FAILED": 500,
    "CONCURRENCY_CONFLICT": 409,
}

# ── Domain Error Codes (IngestionErrorCode) → HTTP Status ──
# Secondary mapper: handles domain codes directly, bypassing
# the ApplicationErrorCode lossy mapping.
_DOMAIN_CODE_TO_STATUS: dict[str, int] = {
    # Not found → 404
    "NEWS_SOURCE_NOT_FOUND": 404,
    "FEED_NOT_FOUND": 404,
    "RAW_ARTICLE_NOT_FOUND": 404,
    "CATEGORY_NOT_FOUND": 404,
    "TOPIC_NOT_FOUND": 404,
    # Conflicts → 409
    "DUPLICATE_NEWS_SOURCE": 409,
    "DUPLICATE_FEED_URL": 409,
    "DUPLICATE_ARTICLE": 409,
    "NEWS_SOURCE_INACTIVE": 409,
    "FEED_INACTIVE": 409,
    "HAS_ACTIVE_FEEDS": 409,
    "FEED_ALREADY_PAUSED": 409,
    "FEED_MAX_RETRIES_EXCEEDED": 409,
    # Validation → 422
    "INVALID_SOURCE_URL": 422,
    "INVALID_ARTICLE_URL": 422,
    "INVALID_LANGUAGE": 422,
    "INVALID_SYNC_POLICY": 422,
    "VALIDATION_ERROR": 422,
    "CYCLE_DETECTED": 422,
    # Other → 500
    "INVALID_STATE": 500,
}


def map_error_code_to_status(error_code: str) -> int:
    """Map an error code string to HTTP status.

    Checks the domain mapper first (more specific), then the application
    mapper, and falls back to 500.

    Args:
        error_code: The error code string (e.g., "NEWS_SOURCE_NOT_FOUND").

    Returns:
        HTTP status code.
    """
    # Try domain codes first (more specific)
    if error_code in _DOMAIN_CODE_TO_STATUS:
        return _DOMAIN_CODE_TO_STATUS[error_code]
    # Then application codes
    if error_code in _APP_CODE_TO_STATUS:
        return _APP_CODE_TO_STATUS[error_code]
    # Fallback
    return 500


# ══════════════════════════════════════════════════════════════════════════════
# Error Type → HTTP Status (for exception handlers)
# ══════════════════════════════════════════════════════════════════════════════

_ERROR_TYPE_TO_STATUS: dict[type, int] = {
    PersistenceError: 503,
    InfrastructureError: 503,
    # FoundationError is the base — catch-all for 500
}

_ERROR_TYPE_TO_PROBLEM_TYPE: dict[type, str] = {
    PersistenceError: "https://api.ai-shorts.dev/errors/service-unavailable",
    InfrastructureError: "https://api.ai-shorts.dev/errors/service-unavailable",
    FoundationError: "https://api.ai-shorts.dev/errors/internal-error",
}


# ══════════════════════════════════════════════════════════════════════════════
# Exception Handlers Registration
# ══════════════════════════════════════════════════════════════════════════════


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app.

    Maps Foundation error hierarchy to RFC 9457 Problem Details responses.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(PersistenceError)
    async def persistence_handler(
        request: Request, exc: PersistenceError
    ) -> JSONResponse:
        """Handle persistence-layer errors → 503 Service Unavailable."""
        logger.error(
            "Persistence error: %s",
            exc,
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return problem_response(
            status=503,
            type_uri="https://api.ai-shorts.dev/errors/service-unavailable",
            title="Service Unavailable",
            detail="A persistence error occurred. Please try again later.",
            instance=str(request.url),
        )

    @app.exception_handler(InfrastructureError)
    async def infrastructure_handler(
        request: Request, exc: InfrastructureError
    ) -> JSONResponse:
        """Handle infrastructure errors → 503 Service Unavailable."""
        logger.error(
            "Infrastructure error: %s",
            exc,
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return problem_response(
            status=503,
            type_uri="https://api.ai-shorts.dev/errors/service-unavailable",
            title="Service Unavailable",
            detail="An infrastructure error occurred. Please try again later.",
            instance=str(request.url),
        )

    @app.exception_handler(FoundationError)
    async def foundation_handler(
        request: Request, exc: FoundationError
    ) -> JSONResponse:
        """Handle Foundation errors → 500 Internal Server Error.

        Catches DomainError, ApplicationError, and base FoundationError.
        """
        logger.error(
            "Foundation error [%s]: %s",
            exc.code,
            exc.message,
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": exc.code,
            },
        )
        return problem_response(
            status=500,
            type_uri="https://api.ai-shorts.dev/errors/internal-error",
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            instance=str(request.url),
        )

    @app.exception_handler(Exception)
    async def generic_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unhandled exceptions → 500 Internal Server Error."""
        logger.exception(
            "Unhandled exception: %s",
            exc,
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return problem_response(
            status=500,
            type_uri="about:blank",
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            instance=str(request.url),
        )
