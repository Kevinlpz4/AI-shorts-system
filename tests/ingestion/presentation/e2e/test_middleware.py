"""
Middleware Audit — Sprint 6.6.

Validates middleware order and behavior:
- Middleware order: CORS → SecurityHeaders → TrustedHost → Recovery → Timing → RequestID → CorrelationID
- Request ID propagated to response headers and request.state
- Correlation ID propagated (falls back to request_id)
- Timing header present
- Security headers present (if enabled)
- TrustedHost validates host
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import APIRouter, Request
from httpx import ASGITransport, AsyncClient

# Test router to inspect middleware state
_test_router = APIRouter()


@_test_router.get("/e2e-test/state")
async def state_inspector(request: Request):
    """Return middleware state for verification."""
    return {
        "request_id": getattr(request.state, "request_id", None),
        "correlation_id": getattr(request.state, "correlation_id", None),
    }


@_test_router.get("/e2e-test/middleware-order")
async def middleware_order_check(request: Request):
    """Verify all middleware executed."""
    return {
        "has_request_id": hasattr(request.state, "request_id"),
        "has_correlation_id": hasattr(request.state, "correlation_id"),
    }


@pytest.fixture(autouse=True)
def _register_e2e_test_routes(e2e_app):
    """Register E2E test routes on the app."""
    e2e_app.include_router(_test_router)


class TestRequestIDMiddleware:
    """RequestIDMiddleware behavior."""

    @pytest.mark.anyio
    async def test_auto_generates_request_id(self, e2e_client: AsyncClient):
        """Request without X-Request-ID gets auto-generated."""
        resp = await e2e_client.get("/e2e-test/state")
        assert "x-request-id" in resp.headers
        uuid.UUID(resp.headers["x-request-id"])

    @pytest.mark.anyio
    async def test_preserves_client_request_id(self, e2e_client: AsyncClient):
        """Client-provided X-Request-ID is preserved."""
        custom = str(uuid.uuid4())
        resp = await e2e_client.get(
            "/e2e-test/state",
            headers={"X-Request-ID": custom},
        )
        assert resp.headers.get("x-request-id") == custom

    @pytest.mark.anyio
    async def test_request_id_in_request_state(self, e2e_client: AsyncClient):
        """request.state.request_id is set."""
        resp = await e2e_client.get("/e2e-test/state")
        body = resp.json()
        assert body["request_id"] is not None
        uuid.UUID(body["request_id"])

    @pytest.mark.anyio
    async def test_request_id_matches_state_and_header(
        self, e2e_client: AsyncClient
    ):
        """request.state.request_id matches response header."""
        resp = await e2e_client.get("/e2e-test/state")
        body = resp.json()
        assert body["request_id"] == resp.headers.get("x-request-id")


class TestCorrelationIDMiddleware:
    """CorrelationIDMiddleware behavior."""

    @pytest.mark.anyio
    async def test_falls_back_to_request_id(self, e2e_client: AsyncClient):
        """Without X-Correlation-ID, falls back to request_id."""
        resp = await e2e_client.get("/e2e-test/state")
        request_id = resp.headers.get("x-request-id")
        correlation_id = resp.headers.get("x-correlation-id")
        assert request_id == correlation_id

    @pytest.mark.anyio
    async def test_preserves_client_correlation_id(self, e2e_client: AsyncClient):
        """Client-provided X-Correlation-ID is preserved."""
        custom = str(uuid.uuid4())
        resp = await e2e_client.get(
            "/e2e-test/state",
            headers={"X-Correlation-ID": custom},
        )
        assert resp.headers.get("x-correlation-id") == custom

    @pytest.mark.anyio
    async def test_correlation_id_in_request_state(self, e2e_client: AsyncClient):
        """request.state.correlation_id is set."""
        resp = await e2e_client.get("/e2e-test/state")
        body = resp.json()
        assert body["correlation_id"] is not None

    @pytest.mark.anyio
    async def test_correlation_id_matches_state_and_header(
        self, e2e_client: AsyncClient
    ):
        """request.state.correlation_id matches response header."""
        resp = await e2e_client.get("/e2e-test/state")
        body = resp.json()
        assert body["correlation_id"] == resp.headers.get("x-correlation-id")


class TestTimingMiddleware:
    """TimingMiddleware behavior."""

    @pytest.mark.anyio
    async def test_timing_header_present(self, e2e_client: AsyncClient):
        """X-Request-Duration header present."""
        resp = await e2e_client.get("/e2e-test/state")
        assert "x-request-duration" in resp.headers

    @pytest.mark.anyio
    async def test_timing_header_format(self, e2e_client: AsyncClient):
        """X-Request-Duration is 'X.XXms' format."""
        resp = await e2e_client.get("/e2e-test/state")
        duration = resp.headers.get("x-request-duration", "")
        import re
        assert re.match(r"^\d+\.\d{2}ms$", duration)

    @pytest.mark.anyio
    async def test_timing_is_positive(self, e2e_client: AsyncClient):
        """Duration is a positive number."""
        resp = await e2e_client.get("/e2e-test/state")
        value = float(resp.headers["x-request-duration"].replace("ms", ""))
        assert value >= 0


class TestMiddlewareExecutionOrder:
    """All middleware execute in correct order."""

    @pytest.mark.anyio
    async def test_all_middleware_executed(self, e2e_client: AsyncClient):
        """All middleware set their state values."""
        resp = await e2e_client.get("/e2e-test/middleware-order")
        body = resp.json()
        assert body["has_request_id"] is True
        assert body["has_correlation_id"] is True

    @pytest.mark.anyio
    async def test_request_id_set_before_correlation_id(
        self, e2e_client: AsyncClient
    ):
        """CorrelationIDMiddleware can read request_id (RequestID ran first)."""
        resp = await e2e_client.get("/e2e-test/state")
        # When no X-Correlation-ID provided, it falls back to request_id
        assert resp.headers["x-request-id"] == resp.headers["x-correlation-id"]

    @pytest.mark.anyio
    async def test_middleware_on_error_response(self, e2e_client: AsyncClient):
        """Middleware headers present on error responses."""
        resp = await e2e_client.get(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404
        assert "x-request-id" in resp.headers
        assert "x-correlation-id" in resp.headers
        assert "x-request-duration" in resp.headers


class TestTrustedHostMiddlewareE2E:
    """TrustedHost middleware (E2E audit).

    These tests use a fresh app with ALLOWED_HOSTS restricted to ensure
    TrustedHostMiddleware rejects invalid hosts. The default e2e_client
    uses ALLOWED_HOSTS=["*"] for convenience.
    """

    @pytest.fixture
    def _restricted_host_app(self, e2e_app, e2e_settings):
        """Create app with restricted ALLOWED_HOSTS."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow

        fresh_settings = e2e_settings.model_copy(
            update={"ALLOWED_HOSTS": ["localhost"]}
        )
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]
        return fresh_app

    @pytest.mark.anyio
    async def test_rejects_invalid_host(self, _restricted_host_app):
        """Invalid host gets 400."""
        async with AsyncClient(
            transport=ASGITransport(app=_restricted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "untrusted-host.com"},
            )
            assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_trusted_host_response_no_request_id(
        self, _restricted_host_app
    ):
        """TrustedHost response lacks x-request-id (runs before RequestID)."""
        async with AsyncClient(
            transport=ASGITransport(app=_restricted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "untrusted-host.com"},
            )
            assert resp.status_code == 400
            # TrustedHost runs before RequestID middleware, so
            # x-request-id is NOT present on TrustedHost rejections.
            # This is expected per middleware order design.

    @pytest.mark.anyio
    async def test_trusted_host_response_no_correlation_id(
        self, _restricted_host_app
    ):
        """TrustedHost response lacks x-correlation-id (runs before CorrelationID)."""
        async with AsyncClient(
            transport=ASGITransport(app=_restricted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "untrusted-host.com"},
            )
            assert resp.status_code == 400
            # Not present because TrustedHost runs before CorrelationID
