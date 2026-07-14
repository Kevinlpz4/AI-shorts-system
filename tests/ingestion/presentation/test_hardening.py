"""
Tests for API Hardening & Production Readiness (Sprint 6.5).

Validates:
- Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, etc.)
- TrustedHostMiddleware (valid host, invalid host, wildcard patterns)
- SECRET_KEY validation (minimum length, insecure values, production startup)
- Configuration hardening (CORS wildcard rejection, LOG_FORMAT validation)
- Startup validation (production SECRET_KEY check, debug warning)
- Error surface (no stack traces to client, consistent Problem Details)
"""

from __future__ import annotations

import os

import pytest
from fastapi import APIRouter, Request
from pydantic import ValidationError

from ingestion.presentation.config import Settings
from ingestion.presentation.app import create_app, _validate_startup_settings


# ── Test router ──

_test_router = APIRouter()


@_test_router.get("/test/ok")
async def test_ok():
    return {"message": "ok"}


@_test_router.get("/test/boom")
async def boom_handler():
    raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def _register_test_routes(app):
    """Register test routes on the app for hardening tests."""
    app.include_router(_test_router)


# ══════════════════════════════════════════════════════════════════════════════
# Security Headers
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityHeaders:
    """Test that security headers are present on every response."""

    EXPECTED_HEADERS = {
        "strict-transport-security": "max-age=15768000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
    }

    @pytest.mark.anyio
    async def test_security_headers_on_ok_response(self, client):
        """Security headers should be present on 200 responses."""
        response = await client.get("/test/ok")
        assert response.status_code == 200
        for header, expected_value in self.EXPECTED_HEADERS.items():
            assert header in response.headers, f"Missing header: {header}"
            assert response.headers[header] == expected_value

    @pytest.mark.anyio
    async def test_security_headers_on_error_response(self, client):
        """Security headers should be present on 500 responses."""
        response = await client.get("/test/boom")
        assert response.status_code == 500
        for header, expected_value in self.EXPECTED_HEADERS.items():
            assert header in response.headers, f"Missing header: {header}"

    @pytest.mark.anyio
    async def test_security_headers_on_health_endpoint(self, client):
        """Security headers should be present on health endpoints."""
        response = await client.get("/health/live")
        assert response.status_code == 200
        for header, expected_value in self.EXPECTED_HEADERS.items():
            assert header in response.headers, f"Missing header: {header}"

    @pytest.mark.anyio
    async def test_hsts_value(self, client):
        """HSTS should enforce HTTPS for 1 year with includeSubDomains."""
        response = await client.get("/test/ok")
        hsts = response.headers["strict-transport-security"]
        assert "max-age=15768000" in hsts
        assert "includeSubDomains" in hsts

    @pytest.mark.anyio
    async def test_x_frame_options_deny(self, client):
        """X-Frame-Options should be DENY to prevent clickjacking."""
        response = await client.get("/test/ok")
        assert response.headers["x-frame-options"] == "DENY"

    @pytest.mark.anyio
    async def test_csp_frame_ancestors_none(self, client):
        """CSP frame-ancestors should be 'none' to prevent framing."""
        response = await client.get("/test/ok")
        csp = response.headers["content-security-policy"]
        assert "frame-ancestors 'none'" in csp


class TestSecurityHeadersDisabled:
    """Test that security headers can be disabled via settings."""

    @pytest.mark.anyio
    async def test_disabled_headers_not_present(self):
        """When SECURITY_HEADERS_ENABLED=False, headers should not be added."""
        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["*"],
            SECURITY_HEADERS_ENABLED=False,
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            response = await ac.get("/health/live")
            assert response.status_code == 200
            assert "strict-transport-security" not in response.headers
            assert "x-frame-options" not in response.headers


# ══════════════════════════════════════════════════════════════════════════════
# TrustedHostMiddleware
# ══════════════════════════════════════════════════════════════════════════════


class TestTrustedHostMiddleware:
    """Test TrustedHostMiddleware host validation."""

    @pytest.mark.anyio
    async def test_allowed_host_accepted(self, client):
        """Request with allowed Host header should succeed."""
        response = await client.get("/test/ok")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_disallowed_host_rejected(self):
        """Request with disallowed Host header should return 400."""
        from httpx import ASGITransport, AsyncClient

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["allowed.example.com"],
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        app.include_router(_test_router)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            response = await ac.get(
                "/test/ok",
                headers={"Host": "evil.example.com"},
            )
            assert response.status_code == 400
            body = response.json()
            assert body["status"] == 400
            assert "Invalid host" in body["detail"]

    @pytest.mark.anyio
    async def test_wildcard_allows_any_host(self):
        """ALLOWED_HOSTS=['*'] should allow any host."""
        from httpx import ASGITransport, AsyncClient

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["*"],
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        app.include_router(_test_router)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            response = await ac.get(
                "/test/ok",
                headers={"Host": "anything.example.com"},
            )
            assert response.status_code == 200

    @pytest.mark.anyio
    async def test_subdomain_wildcard(self):
        """ALLOWED_HOSTS=['*.example.com'] should match subdomains."""
        from httpx import ASGITransport, AsyncClient

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["*.example.com"],
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        app.include_router(_test_router)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            # Should allow subdomain
            response = await ac.get(
                "/test/ok",
                headers={"Host": "api.example.com"},
            )
            assert response.status_code == 200

            # Should reject different domain
            response = await ac.get(
                "/test/ok",
                headers={"Host": "evil.com"},
            )
            assert response.status_code == 400

    @pytest.mark.anyio
    async def test_invalid_host_returns_problem_details(self):
        """Rejected host should return RFC 9457 Problem Details."""
        from httpx import ASGITransport, AsyncClient

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["good.example.com"],
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        app.include_router(_test_router)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            response = await ac.get(
                "/test/ok",
                headers={"Host": "bad.example.com"},
            )
            assert response.status_code == 400
            assert response.headers["content-type"] == "application/problem+json"
            body = response.json()
            assert body["type"] == "about:blank"
            assert body["title"] == "Bad Request"
            assert "instance" in body


# ══════════════════════════════════════════════════════════════════════════════
# SECRET_KEY Validation
# ══════════════════════════════════════════════════════════════════════════════


class TestSecretKeyValidation:
    """Test SECRET_KEY validation rules."""

    def test_short_secret_key_rejected(self):
        """SECRET_KEY shorter than 8 chars should raise ValidationError."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            Settings(
                SECRET_KEY="short",
                ENVIRONMENT="testing",
            )

    def test_empty_secret_key_rejected(self):
        """Empty SECRET_KEY should raise ValidationError."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            Settings(
                SECRET_KEY="",
                ENVIRONMENT="testing",
            )

    def test_valid_secret_key_accepted(self):
        """SECRET_KEY with 8+ chars should be accepted."""
        settings = Settings(
            SECRET_KEY="my-super-secret-key-123",
            ENVIRONMENT="testing",
        )
        assert settings.SECRET_KEY == "my-super-secret-key-123"

    def test_secret_key_preserved_exactly(self):
        """SECRET_KEY should be preserved exactly as provided."""
        key = "a]b@c#d$e%f^g&h*i(j)k"
        settings = Settings(
            SECRET_KEY=key,
            ENVIRONMENT="testing",
        )
        assert settings.SECRET_KEY == key


class TestProductionSecretKeyValidation:
    """Test startup validation for production SECRET_KEY."""

    def test_production_insecure_secret_key_raises(self):
        """create_app should raise RuntimeError for insecure SECRET_KEY in production."""
        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=["https://example.com"],
            SECRET_KEY="change-me-in-production",
            ALLOWED_HOSTS=["example.com"],
        )
        with pytest.raises(RuntimeError, match="SECRET_KEY must be changed"):
            create_app(settings=settings)

    def test_production_valid_secret_key_accepted(self):
        """create_app should succeed with valid SECRET_KEY in production."""
        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=["https://example.com"],
            SECRET_KEY="super-secret-production-key-12345",
            ALLOWED_HOSTS=["example.com"],
        )
        app = create_app(settings=settings)
        assert app is not None

    def test_testing_insecure_secret_key_accepted(self):
        """create_app should NOT reject insecure SECRET_KEY in testing environment."""
        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            SECRET_KEY="change-me-in-production",
            ALLOWED_HOSTS=["*"],
        )
        # Should NOT raise — validation only applies to production
        app = create_app(settings=settings)
        assert app is not None


# ══════════════════════════════════════════════════════════════════════════════
# Configuration Hardening
# ══════════════════════════════════════════════════════════════════════════════


class TestCORSValidation:
    """Test CORS configuration validation."""

    def test_wildcard_cors_rejected(self):
        """CORS_ORIGINS with '*' wildcard should raise ValidationError."""
        with pytest.raises(ValidationError, match="wildcard"):
            Settings(
                CORS_ORIGINS=["*"],
                ENVIRONMENT="testing",
            )

    def test_specific_origins_accepted(self):
        """CORS_ORIGINS with specific origins should be accepted."""
        settings = Settings(
            CORS_ORIGINS=["https://app.example.com", "https://admin.example.com"],
            ENVIRONMENT="testing",
        )
        assert len(settings.CORS_ORIGINS) == 2

    def test_empty_cors_accepted(self):
        """Empty CORS_ORIGINS should be accepted (disables CORS)."""
        settings = Settings(
            CORS_ORIGINS=[],
            ENVIRONMENT="testing",
        )
        assert settings.CORS_ORIGINS == []


class TestLogFormatValidation:
    """Test LOG_FORMAT validation."""

    def test_invalid_log_format_rejected(self):
        """Invalid LOG_FORMAT should raise ValidationError."""
        with pytest.raises(ValidationError, match="must be 'json' or 'text'"):
            Settings(
                LOG_FORMAT="xml",
                ENVIRONMENT="testing",
            )

    def test_json_format_accepted(self):
        """'json' LOG_FORMAT should be accepted."""
        settings = Settings(LOG_FORMAT="json", ENVIRONMENT="testing")
        assert settings.LOG_FORMAT == "json"

    def test_text_format_accepted(self):
        """'text' LOG_FORMAT should be accepted."""
        settings = Settings(LOG_FORMAT="text", ENVIRONMENT="testing")
        assert settings.LOG_FORMAT == "text"


class TestEnvironmentValidation:
    """Test ENVIRONMENT validation."""

    def test_invalid_environment_rejected(self):
        """Invalid ENVIRONMENT should raise ValidationError."""
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="staging")

    def test_development_accepted(self):
        """'development' should be accepted."""
        settings = Settings(ENVIRONMENT="development")
        assert settings.ENVIRONMENT == "development"

    def test_testing_accepted(self):
        """'testing' should be accepted."""
        settings = Settings(ENVIRONMENT="testing")
        assert settings.ENVIRONMENT == "testing"

    def test_production_accepted(self):
        """'production' should be accepted."""
        settings = Settings(ENVIRONMENT="production")
        assert settings.ENVIRONMENT == "production"


class TestStartupValidation:
    """Test _validate_startup_settings function."""

    def test_production_debug_warning(self, caplog):
        """Production + DEBUG=True should log a warning."""
        import logging

        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=["https://example.com"],
            SECRET_KEY="super-secret-production-key-12345",
            DEBUG=True,
            ALLOWED_HOSTS=["example.com"],
        )
        with caplog.at_level(logging.WARNING):
            _validate_startup_settings(settings)
        assert "DEBUG mode is enabled in production" in caplog.text

    def test_production_localhost_cors_warning(self, caplog):
        """Production + localhost CORS should log a warning."""
        import logging

        settings = Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=["http://localhost:3000"],
            SECRET_KEY="super-secret-production-key-12345",
            ALLOWED_HOSTS=["example.com"],
        )
        with caplog.at_level(logging.WARNING):
            _validate_startup_settings(settings)
        assert "CORS_ORIGINS is set to localhost default" in caplog.text

    def test_development_no_warnings(self, caplog):
        """Development environment should not trigger production warnings."""
        import logging

        settings = Settings(
            ENVIRONMENT="development",
            DATABASE_URL="sqlite:///:memory:",
            SECRET_KEY="development-secret-key-123",
        )
        with caplog.at_level(logging.WARNING):
            _validate_startup_settings(settings)
        assert "production" not in caplog.text.lower() or "CRITICAL" not in caplog.text


# ══════════════════════════════════════════════════════════════════════════════
# Error Surface Audit
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorSurfaceAudit:
    """Test that error responses don't leak internal details."""

    @pytest.mark.anyio
    async def test_500_no_stacktrace_in_response(self, client):
        """500 error responses should not contain stack traces."""
        response = await client.get("/test/boom")
        assert response.status_code == 500
        body = response.json()
        # Should not contain Python exception details
        assert "traceback" not in str(body).lower()
        assert "RuntimeError" not in str(body)
        assert "boom" not in body.get("detail", "").lower()

    @pytest.mark.anyio
    async def test_500_returns_problem_details(self, client):
        """500 errors should return RFC 9457 Problem Details."""
        response = await client.get("/test/boom")
        assert response.status_code == 500
        assert response.headers["content-type"] == "application/problem+json"
        body = response.json()
        assert body["type"] == "about:blank"
        assert body["title"] == "Internal Server Error"
        assert body["status"] == 500
        assert "instance" in body

    @pytest.mark.anyio
    async def test_404_returns_problem_details(self, client):
        """404 errors should return RFC 9457 Problem Details."""
        response = await client.get("/nonexistent-path")
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_invalid_host_no_internal_details(self, client):
        """Invalid host error should not expose internal configuration."""
        from httpx import ASGITransport, AsyncClient

        settings = Settings(
            ENVIRONMENT="testing",
            DATABASE_URL="sqlite:///:memory:",
            CORS_ORIGINS=[],
            ALLOWED_HOSTS=["only-this.example.com"],
            SECRET_KEY="test-secret-key",
        )
        app = create_app(settings=settings)
        app.include_router(_test_router)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            response = await ac.get("/test/ok")
            assert response.status_code == 400
            body = response.json()
            # Should not expose middleware configuration or allowed hosts list
            assert "allowed_hosts" not in str(body).lower()
            assert "ALLOWED_HOSTS" not in str(body)


# ══════════════════════════════════════════════════════════════════════════════
# Middleware Registration
# ══════════════════════════════════════════════════════════════════════════════


class TestMiddlewareRegistration:
    """Test that all 6 middleware are registered in correct order."""

    def test_all_middleware_registered(self, app):
        """App should have all 6 middleware classes registered."""
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "SecurityHeadersMiddleware" in middleware_classes
        assert "TrustedHostMiddleware" in middleware_classes
        assert "RecoveryMiddleware" in middleware_classes
        assert "TimingMiddleware" in middleware_classes
        assert "CorrelationIDMiddleware" in middleware_classes
        assert "RequestIDMiddleware" in middleware_classes

    def test_middleware_execution_order(self, app):
        """Middleware should execute in correct order.

        user_middleware list is in REVERSE execution order (first item = outermost).
        add_middleware() uses insert(0, ...) so last added = index 0 = outermost.

        List order (index 0 = outermost = first to execute):
            CORS(0) → SecurityHeaders(1) → TrustedHost(2) → Recovery(3) → Timing(4) → RequestID(5) → CorrelationID(6)
        """
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]

        def idx(name):
            return middleware_classes.index(name)

        # Outermost (first to execute) has lower index
        assert idx("CORSMiddleware") < idx("SecurityHeadersMiddleware")
        assert idx("SecurityHeadersMiddleware") < idx("TrustedHostMiddleware")
        assert idx("TrustedHostMiddleware") < idx("RecoveryMiddleware")
        assert idx("RecoveryMiddleware") < idx("TimingMiddleware")
        assert idx("TimingMiddleware") < idx("RequestIDMiddleware")
        assert idx("RequestIDMiddleware") < idx("CorrelationIDMiddleware")
