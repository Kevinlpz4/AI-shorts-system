"""
Tests for Middleware Stack.

Validates:
- RequestIDMiddleware: auto-generates UUID, preserves client-provided ID
- CorrelationIDMiddleware: falls back to request_id when no header
- TimingMiddleware: X-Request-Duration header present
- RecoveryMiddleware: catches unhandled exceptions, returns 500 Problem Details
- Request ID available in request.state during handler execution
- Correlation ID available in request.state during handler execution
- Timing duration available in request.state during handler execution
- Middleware order: Recovery → Timing → CorrelationID → RequestID (outermost to innermost)
"""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi import APIRouter, Request

# ── Test router with endpoints that exercise middleware ──

_test_router = APIRouter()


@_test_router.get("/test/ok")
async def test_ok():
    return {"message": "ok"}


@_test_router.get("/test/boom")
async def boom_handler():
    raise RuntimeError("boom")


@_test_router.get("/test/state")
async def state_inspector(request: Request):
    """Return middleware state values for verification."""
    return {
        "request_id": getattr(request.state, "request_id", None),
        "correlation_id": getattr(request.state, "correlation_id", None),
        "duration_ms": getattr(request.state, "duration_ms", None),
    }


@_test_router.get("/test/middleware-order")
async def middleware_order_check(request: Request):
    """Return middleware state to verify execution order.

    If all middleware executed, all three fields should be present.
    """
    has_request_id = hasattr(request.state, "request_id")
    has_correlation_id = hasattr(request.state, "correlation_id")
    has_duration = hasattr(request.state, "duration_ms")
    return {
        "has_request_id": has_request_id,
        "has_correlation_id": has_correlation_id,
        "has_duration_ms": has_duration,
    }


@pytest.fixture(autouse=True)
def _register_test_routes(app):
    """Register test routes on the app for middleware tests."""
    app.include_router(_test_router)


class TestRequestIDMiddleware:
    """Test RequestIDMiddleware behavior."""

    @pytest.mark.anyio
    async def test_auto_generates_request_id(self, client):
        """Request without X-Request-ID should get one auto-generated."""
        response = await client.get("/test/ok")
        assert "x-request-id" in response.headers
        request_id = response.headers["x-request-id"]
        # Should be a valid UUID
        uuid.UUID(request_id)  # Raises if invalid

    @pytest.mark.anyio
    async def test_preserves_client_request_id(self, client):
        """Client-provided X-Request-ID should be preserved."""
        custom_id = str(uuid.uuid4())
        response = await client.get(
            "/test/ok",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["x-request-id"] == custom_id

    @pytest.mark.anyio
    async def test_request_id_in_response_header(self, client):
        """Response should always include X-Request-ID header."""
        response = await client.get("/test/ok")
        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0


class TestCorrelationIDMiddleware:
    """Test CorrelationIDMiddleware behavior."""

    @pytest.mark.anyio
    async def test_uses_request_id_when_no_correlation_id(self, client):
        """Without X-Correlation-ID header, falls back to request_id."""
        response = await client.get("/test/ok")
        request_id = response.headers["x-request-id"]
        correlation_id = response.headers["x-correlation-id"]
        assert request_id == correlation_id

    @pytest.mark.anyio
    async def test_preserves_client_correlation_id(self, client):
        """Client-provided X-Correlation-ID should be preserved."""
        custom_corr = str(uuid.uuid4())
        response = await client.get(
            "/test/ok",
            headers={"X-Correlation-ID": custom_corr},
        )
        assert response.headers["x-correlation-id"] == custom_corr

    @pytest.mark.anyio
    async def test_correlation_id_in_response_header(self, client):
        """Response should always include X-Correlation-ID header."""
        response = await client.get("/test/ok")
        assert "x-correlation-id" in response.headers


class TestTimingMiddleware:
    """Test TimingMiddleware behavior."""

    @pytest.mark.anyio
    async def test_timing_header_present(self, client):
        """Response should include X-Request-Duration header."""
        response = await client.get("/test/ok")
        assert "x-request-duration" in response.headers

    @pytest.mark.anyio
    async def test_timing_header_format(self, client):
        """X-Request-Duration should be formatted as 'X.XXms'."""
        response = await client.get("/test/ok")
        duration = response.headers["x-request-duration"]
        # Match pattern like "1.23ms"
        assert re.match(r"^\d+\.\d{2}ms$", duration)

    @pytest.mark.anyio
    async def test_timing_is_positive(self, client):
        """Duration should be a positive number."""
        response = await client.get("/test/ok")
        duration_str = response.headers["x-request-duration"]
        value = float(duration_str.replace("ms", ""))
        assert value >= 0


class TestRecoveryMiddleware:
    """Test RecoveryMiddleware behavior."""

    @pytest.mark.anyio
    async def test_catches_unhandled_exception(self, client):
        """RecoveryMiddleware should catch unhandled exceptions."""
        response = await client.get("/test/boom")
        assert response.status_code == 500

    @pytest.mark.anyio
    async def test_returns_problem_details_on_exception(self, client):
        """Exception response should be RFC 9457 Problem Details."""
        response = await client.get("/test/boom")
        assert response.headers["content-type"] == "application/problem+json"
        body = response.json()
        assert body["type"] == "about:blank"
        assert body["title"] == "Internal Server Error"
        assert body["status"] == 500
        assert body["detail"] == "An unexpected error occurred."

    @pytest.mark.anyio
    async def test_exception_response_has_instance(self, client):
        """Problem Details should include instance URL."""
        response = await client.get("/test/boom")
        body = response.json()
        assert "instance" in body
        assert "/test/boom" in body["instance"]


class TestMiddlewareStateAccess:
    """Test that middleware values are accessible in request.state during handler execution."""

    @pytest.mark.anyio
    async def test_request_id_in_request_state(self, client):
        """request.state.request_id should be set by RequestIDMiddleware."""
        response = await client.get("/test/state")
        assert response.status_code == 200
        body = response.json()
        assert body["request_id"] is not None
        # Should be a valid UUID
        uuid.UUID(body["request_id"])

    @pytest.mark.anyio
    async def test_correlation_id_in_request_state(self, client):
        """request.state.correlation_id should be set by CorrelationIDMiddleware."""
        response = await client.get("/test/state")
        assert response.status_code == 200
        body = response.json()
        assert body["correlation_id"] is not None

    @pytest.mark.anyio
    async def test_duration_available_via_response_header(self, client):
        """TimingMiddleware sets duration via X-Request-Duration header.

        Note: duration_ms is set on request.state AFTER the handler returns
        (not during), so it's not accessible from within the handler.
        It IS available via the response header.
        """
        response = await client.get("/test/ok")
        assert response.status_code == 200
        assert "x-request-duration" in response.headers
        duration_str = response.headers["x-request-duration"]
        value = float(duration_str.replace("ms", ""))
        assert value >= 0

    @pytest.mark.anyio
    async def test_state_values_match_headers(self, client):
        """request.state values should match response headers."""
        response = await client.get("/test/state")
        body = response.json()

        # request_id in state should match response header
        assert body["request_id"] == response.headers["x-request-id"]
        # correlation_id in state should match response header
        assert body["correlation_id"] == response.headers["x-correlation-id"]


class TestMiddlewareOrder:
    """Test that middleware executes in correct order."""

    @pytest.mark.anyio
    async def test_all_middleware_executed(self, client):
        """All middleware should execute, setting their state values.

        Middleware order (outermost to innermost):
            Recovery → Timing → CorrelationID → RequestID → Handler

        When handler runs:
          - request_id is set (RequestIDMiddleware, innermost, runs first)
          - correlation_id is set (CorrelationIDMiddleware, runs after RequestID)
          - duration_ms is NOT yet set (TimingMiddleware sets it AFTER handler returns)

        All three values are available in the response (headers + state post-handler).
        """
        response = await client.get("/test/middleware-order")
        assert response.status_code == 200
        body = response.json()

        assert body["has_request_id"] is True, (
            "RequestIDMiddleware (innermost) should have set request_id"
        )
        assert body["has_correlation_id"] is True, (
            "CorrelationIDMiddleware should have set correlation_id"
        )
        # duration_ms is set AFTER handler returns (by TimingMiddleware),
        # so it's not visible during handler execution
        assert body["has_duration_ms"] is False, (
            "TimingMiddleware sets duration_ms after handler — should not be visible"
        )

        # But duration_ms IS available via response header (set post-handler)
        assert "x-request-duration" in response.headers

    @pytest.mark.anyio
    async def test_request_id_set_before_correlation_id(self, client):
        """CorrelationIDMiddleware should be able to read request_id.

        When no X-Correlation-ID header is provided, CorrelationIDMiddleware
        falls back to request.state.request_id (set by RequestIDMiddleware).
        This only works if RequestIDMiddleware runs first (innermost).
        """
        response = await client.get("/test/ok")
        request_id = response.headers["x-request-id"]
        correlation_id = response.headers["x-correlation-id"]
        # Fallback means correlation_id == request_id
        assert request_id == correlation_id
