"""
Response timing middleware.

Measures request processing time and adds X-Response-Time header
to every response in milliseconds.
"""
from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds X-Response-Time header to every response.

    Measures wall-clock time from request reception to response
    completion using time.perf_counter for high-resolution timing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
        return response
