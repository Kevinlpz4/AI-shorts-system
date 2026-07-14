"""
Middleware Stack — Request lifecycle middleware.

Six middleware applied in EXACT order (outermost first, i.e., last
``add_middleware`` = first to execute):

1. **SecurityHeadersMiddleware**: Add security headers to every response.
2. **TrustedHostMiddleware**: Validate Host header against allowed hosts.
3. **RecoveryMiddleware**: Catch ALL unhandled exceptions, return 500 Problem Details.
4. **TimingMiddleware**: Measure request duration, add ``X-Request-Duration``.
5. **CorrelationIDMiddleware**: Read ``X-Correlation-ID`` or use request_id.
6. **RequestIDMiddleware**: Read ``X-Request-ID`` from header or generate UUID v4.

Usage::

    app.add_middleware(SecurityHeadersMiddleware)  # outermost (first to execute)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[...])
    app.add_middleware(RecoveryMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestIDMiddleware)          # innermost (last to execute)
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

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


# ============================================================================
# Security Headers Middleware
# ============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response.

    Headers added:
    - Strict-Transport-Security: 15768000; includeSubDomains (1 year)
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
    - Permissions-Policy: camera=(), microphone=(), geolocation=()

    Configuration via ``Settings.SECURITY_HEADERS_ENABLED``.
    """

    DEFAULT_HEADERS: dict[str, str] = {
        "Strict-Transport-Security": "max-age=15768000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }

    def __init__(self, app: ASGIApp, enabled: bool = True) -> None:
        super().__init__(app)
        self._enabled = enabled

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if self._enabled:
            for header, value in self.DEFAULT_HEADERS.items():
                response.headers[header] = value
        return response


# ============================================================================
# Trusted Host Middleware (lightweight wrapper)
# ============================================================================


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """Validate Host header against a list of allowed hosts.

    Rejects requests with a ``Host`` header not in the allowed list
    with a ``400 Bad Request`` Problem Details response.

    Configuration via ``Settings.ALLOWED_HOSTS``.
    """

    def __init__(self, app: ASGIApp, allowed_hosts: list[str] | None = None) -> None:
        super().__init__(app)
        self._allowed_hosts = allowed_hosts or ["*"]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        host = request.headers.get("host", "")
        # Strip port for comparison (Host header may include port)
        hostname = host.split(":")[0] if host else ""

        # Check if any allowed host pattern matches
        allowed = False
        for pattern in self._allowed_hosts:
            if pattern == "*":
                allowed = True
                break
            if pattern.startswith("*."):
                # Wildcard subdomain: *.example.com matches foo.example.com
                suffix = pattern[1:]  # .example.com
                if hostname.endswith(suffix) or hostname == pattern[2:]:
                    allowed = True
                    break
            if hostname == pattern:
                allowed = True
                break

        if not allowed:
            return JSONResponse(
                status_code=400,
                content={
                    "type": "about:blank",
                    "title": "Bad Request",
                    "status": 400,
                    "detail": f"Invalid host: {hostname}",
                    "instance": str(request.url),
                },
                media_type="application/problem+json",
            )

        return await call_next(request)
