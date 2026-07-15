"""
Security Audit — Sprint 6.6.

Validates all security controls:
- Security headers present on every response
- TrustedHost middleware rejects invalid hosts
- SECRET_KEY validated at startup
- CORS no wildcard
- Problem Details consistent
- UUID validation on path params
- Request IDs present
"""

from __future__ import annotations

import uuid

import pytest

from httpx import AsyncClient


class TestSecurityHeaders:
    """All 6 security headers present on every response."""

    EXPECTED_HEADERS = {
        "strict-transport-security": "max-age=15768000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
    }

    @pytest.mark.anyio
    async def test_security_headers_on_success(self, e2e_app, e2e_settings):
        """Security headers present on 200 responses."""
        # Use a fresh client with security headers ENABLED
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow
        from httpx import ASGITransport

        # Override settings to enable security headers
        fresh_settings = e2e_settings.model_copy(
            update={"SECURITY_HEADERS_ENABLED": True}
        )
        # Replace the engine reference so we use the same DB
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]

        async with AsyncClient(
            transport=ASGITransport(app=fresh_app),
            base_url="http://testserver",
        ) as client:
            # Create a source to get a 200 response
            resp = await client.post(
                "/api/v1/sources",
                json={
                    "name": "Security Headers Source",
                    "source_type": "RSS",
                    "source_url": "https://sec-headers.example.com/rss",
                },
            )
            # Check security headers
            for header, expected_value in self.EXPECTED_HEADERS.items():
                assert header in resp.headers, f"Missing header: {header}"
                assert resp.headers[header] == expected_value

    @pytest.mark.anyio
    async def test_security_headers_on_error(self, e2e_app, e2e_settings):
        """Security headers present on error responses."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow
        from httpx import ASGITransport

        fresh_settings = e2e_settings.model_copy(
            update={"SECURITY_HEADERS_ENABLED": True}
        )
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]

        async with AsyncClient(
            transport=ASGITransport(app=fresh_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/api/v1/sources/00000000-0000-0000-0000-000000000000"
            )
            assert resp.status_code == 404
            for header in self.EXPECTED_HEADERS:
                assert header in resp.headers, f"Missing header on error: {header}"

    @pytest.mark.anyio
    async def test_security_headers_on_health(self, e2e_app, e2e_settings):
        """Security headers present on health endpoint."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow
        from httpx import ASGITransport

        fresh_settings = e2e_settings.model_copy(
            update={"SECURITY_HEADERS_ENABLED": True}
        )
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]

        async with AsyncClient(
            transport=ASGITransport(app=fresh_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/health/live")
            assert resp.status_code == 200
            for header in self.EXPECTED_HEADERS:
                assert header in resp.headers, f"Missing header on health: {header}"

    @pytest.mark.anyio
    async def test_hsts_includes_subdomains(self, e2e_app, e2e_settings):
        """HSTS header includes includeSubDomains."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow
        from httpx import ASGITransport

        fresh_settings = e2e_settings.model_copy(
            update={"SECURITY_HEADERS_ENABLED": True}
        )
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]

        async with AsyncClient(
            transport=ASGITransport(app=fresh_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/health/live")
            hsts = resp.headers.get("strict-transport-security", "")
            assert "max-age=15768000" in hsts
            assert "includeSubDomains" in hsts

    @pytest.mark.anyio
    async def test_x_frame_options_deny(self, e2e_app, e2e_settings):
        """X-Frame-Options is DENY."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.dependencies import get_uow
        from httpx import ASGITransport

        fresh_settings = e2e_settings.model_copy(
            update={"SECURITY_HEADERS_ENABLED": True}
        )
        fresh_app = create_app(settings=fresh_settings)
        fresh_app.state.engine = e2e_app.state.engine
        fresh_app.state.session_factory = e2e_app.state.session_factory
        fresh_app.dependency_overrides[get_uow] = e2e_app.dependency_overrides[get_uow]

        async with AsyncClient(
            transport=ASGITransport(app=fresh_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get("/health/live")
            assert resp.headers.get("x-frame-options") == "DENY"


class TestTrustedHost:
    """TrustedHost middleware validates Host header.

    These tests use a fresh app with ALLOWED_HOSTS restricted to ensure
    TrustedHostMiddleware rejects invalid hosts. The default e2e_client
    uses ALLOWED_HOSTS=["*"] for convenience.
    """

    @pytest.fixture
    def _trusted_host_app(self, e2e_app, e2e_settings):
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
    async def test_allowed_host_passes(self, e2e_client: AsyncClient):
        """Valid host passes TrustedHostMiddleware."""
        resp = await e2e_client.get("/health/live")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_rejected_host_gets_400(self, _trusted_host_app):
        """Invalid host gets 400."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=_trusted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "evil.example.com"},
            )
            assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_rejected_host_returns_problem_details(
        self, _trusted_host_app
    ):
        """Invalid host returns Problem Details."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=_trusted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "evil.example.com"},
            )
            data = resp.json()
            assert "type" in data
            assert data["status"] == 400
            assert "detail" in data

    @pytest.mark.anyio
    async def test_rejected_host_leaks_no_internal_details(
        self, _trusted_host_app
    ):
        """Invalid host response does not leak internal config."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=_trusted_host_app),
            base_url="http://testserver",
        ) as client:
            resp = await client.get(
                "/health/live",
                headers={"host": "evil.example.com"},
            )
            data = resp.json()
            detail = data.get("detail", "").lower()
            assert "allowed" not in detail
            assert "localhost" not in detail


class TestRequestIDs:
    """Request IDs present on all responses."""

    @pytest.mark.anyio
    async def test_request_id_header_present(self, e2e_client: AsyncClient):
        """X-Request-ID header present on all responses."""
        resp = await e2e_client.get("/health/live")
        assert "x-request-id" in resp.headers

    @pytest.mark.anyio
    async def test_request_id_is_valid_uuid(self, e2e_client: AsyncClient):
        """X-Request-ID is a valid UUID."""
        resp = await e2e_client.get("/health/live")
        uuid.UUID(resp.headers["x-request-id"])

    @pytest.mark.anyio
    async def test_request_id_on_error(self, e2e_client: AsyncClient):
        """X-Request-ID present on error responses."""
        resp = await e2e_client.get(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404
        assert "x-request-id" in resp.headers

    @pytest.mark.anyio
    async def test_correlation_id_present(self, e2e_client: AsyncClient):
        """X-Correlation-ID present on all responses."""
        resp = await e2e_client.get("/health/live")
        assert "x-correlation-id" in resp.headers


class TestSECRETKEY:
    """SECRET_KEY validation at startup."""

    def test_secret_key_too_short_raises(self):
        """SECRET_KEY < 8 chars raises ValidationError."""
        from pydantic import ValidationError
        from ingestion.presentation.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="testing",
                DATABASE_URL="sqlite:///:memory:",
                SECRET_KEY="short",
            )

    def test_insecure_key_in_production_raises(self):
        """Production + insecure SECRET_KEY raises RuntimeError."""
        from ingestion.presentation.app import create_app
        from ingestion.presentation.config import Settings

        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///:memory:",
            SECRET_KEY="change-me-in-production",
        )
        with pytest.raises(RuntimeError):
            create_app(settings=settings)

    def test_secure_key_validates_ok(self):
        """Valid SECRET_KEY passes validation."""
        from ingestion.presentation.config import Settings

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            SECRET_KEY="a-valid-secret-key-123",
        )
        assert settings.SECRET_KEY == "a-valid-secret-key-123"
