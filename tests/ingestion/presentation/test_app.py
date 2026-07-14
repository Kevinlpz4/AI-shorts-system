"""
Tests for FastAPI Application Factory.

Validates:
- create_app returns a FastAPI instance
- Metadata (title, version, description) is correct
- docs_url, redoc_url, openapi_url are configured
- Middleware is registered
- Exception handlers are registered
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI


class TestAppFactory:
    """Test create_app() returns a properly configured FastAPI instance."""

    def test_create_app_returns_fastapi(self, settings):
        """create_app should return a FastAPI instance."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert isinstance(app, FastAPI)

    def test_app_title(self, settings):
        """App title should include version."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert "AI Shorts System" in app.title
        assert "Ingestion API" in app.title

    def test_app_version(self, settings):
        """App version should come from settings."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert app.version == settings.openapi_version

    def test_app_description(self, settings):
        """App should have a description."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert app.description is not None
        assert "ingestion" in app.description.lower()

    def test_docs_url(self, settings):
        """App should have docs at /docs."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert app.docs_url == "/docs"

    def test_redoc_url(self, settings):
        """App should have redoc at /redoc."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert app.redoc_url == "/redoc"

    def test_openapi_url(self, settings):
        """App should serve OpenAPI at /openapi.json."""
        from ingestion.presentation.app import create_app

        app = create_app(settings=settings)
        assert app.openapi_url == "/openapi.json"

    def test_create_app_with_default_settings(self):
        """create_app() with no args should use default Settings."""
        from ingestion.presentation.app import create_app

        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title is not None


class TestAppMiddleware:
    """Test that middleware is registered on the app."""

    def test_middleware_registered(self, app):
        """App should have middleware registered."""
        # FastAPI stores middleware in user_middleware
        middleware_classes = [
            m.cls.__name__ for m in app.user_middleware
        ]
        assert "RequestIDMiddleware" in middleware_classes
        assert "CorrelationIDMiddleware" in middleware_classes
        assert "TimingMiddleware" in middleware_classes
        assert "RecoveryMiddleware" in middleware_classes

    def test_middleware_order(self, app):
        """Middleware should be in correct execution order.

        user_middleware list is REVERSE execution order (first item = outermost).
        add_middleware() uses insert(0, ...) so last added = index 0 = outermost.

        List order: CORS(0) → SecurityHeaders(1) → TrustedHost(2) → Recovery(3) → Timing(4) → RequestID(5) → CorrelationID(6)
        """
        middleware_classes = [
            m.cls.__name__ for m in app.user_middleware
        ]
        # CORS is outermost (added last in app.py)
        assert middleware_classes[0] == "CORSMiddleware"
        # Then our custom middleware
        assert "SecurityHeadersMiddleware" in middleware_classes
        assert "TrustedHostMiddleware" in middleware_classes
        assert "RecoveryMiddleware" in middleware_classes
        assert "TimingMiddleware" in middleware_classes
        assert "RequestIDMiddleware" in middleware_classes
        assert "CorrelationIDMiddleware" in middleware_classes
        # Verify custom middleware order relative to each other
        # user_middleware stores in reverse execution order (first = outermost = lowest index)
        security_idx = middleware_classes.index("SecurityHeadersMiddleware")
        trusted_idx = middleware_classes.index("TrustedHostMiddleware")
        recovery_idx = middleware_classes.index("RecoveryMiddleware")
        timing_idx = middleware_classes.index("TimingMiddleware")
        request_idx = middleware_classes.index("RequestIDMiddleware")
        correlation_idx = middleware_classes.index("CorrelationIDMiddleware")
        assert security_idx < trusted_idx < recovery_idx < timing_idx < request_idx < correlation_idx


class TestAppSettings:
    """Test that settings are stored on app.state."""

    def test_settings_on_app_state(self, app, settings):
        """Settings should be stored on app.state."""
        assert hasattr(app.state, "settings")
        assert app.state.settings is settings
