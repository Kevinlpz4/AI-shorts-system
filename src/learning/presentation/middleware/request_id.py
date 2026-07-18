"""
Request ID + Correlation ID middleware.

Every request gets a unique X-Request-ID. If the client provides one,
it's reused. X-Correlation-ID links related requests across services.
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID and X-Correlation-ID to every request/response.

    If the incoming request includes an X-Request-ID header, it is
    preserved. Otherwise, a new UUID4 is generated. The X-Correlation-ID
    defaults to the request ID if not provided.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id = request.headers.get("X-Correlation-ID", request_id)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        return response
