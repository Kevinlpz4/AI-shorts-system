"""
Middleware Stack — Request lifecycle middleware.

Four middleware applied in EXACT order (outermost first, i.e., last
``add_middleware`` = first to execute):

1. **RequestIDMiddleware**: Read ``X-Request-ID`` from header or generate UUID v4.
2. **CorrelationIDMiddleware**: Read ``X-Correlation-ID`` or use request_id.
3. **TimingMiddleware**: Measure request duration, add ``X-Request-Duration``.
4. **RecoveryMiddleware**: Catch ALL unhandled exceptions, return 500 Problem Details.

Usage::

    app.add_middleware(RecoveryMiddleware)     # outermost (first to execute)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestIDMiddleware)     # innermost (last to execute)
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Read or generate a unique request ID.

    - Reads ``X-Request-ID`` from the incoming request header.
    - If absent, generates a UUID v4.
    - Stores on ``request.state.request_id``.
    - Sets on the response header.
    """

    HEADER = "X-Request-ID"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get(self.HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.HEADER] = request_id
        return response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Read or derive a correlation ID for request tracing.

    - Reads ``X-Correlation-ID`` from the incoming request header.
    - If absent, uses ``request.state.request_id`` (set by RequestIDMiddleware).
    - Stores on ``request.state.correlation_id``.
    - Sets on the response header.
    """

    HEADER = "X-Correlation-ID"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = request.headers.get(
            self.HEADER,
            getattr(request.state, "request_id", None),
        )
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[self.HEADER] = correlation_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure request processing duration.

    - Measures time from before to after handler execution.
    - Sets ``X-Request-Duration`` header (milliseconds, 2 decimal places).
    - Stores ``request.state.duration_ms`` as a float.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Duration"] = f"{duration_ms:.2f}ms"
        request.state.duration_ms = duration_ms
        return response


class RecoveryMiddleware(BaseHTTPMiddleware):
    """Catch ALL unhandled exceptions and return 500 Problem Details.

    This is the OUTERMOST middleware — it catches exceptions from
    all other middleware and handlers. Never lets exceptions propagate.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception in middleware/handler",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            body = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred.",
                "instance": str(request.url),
            }
            return JSONResponse(
                status_code=500,
                content=body,
                media_type="application/problem+json",
            )
