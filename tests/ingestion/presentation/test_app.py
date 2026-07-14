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

        Last added = first executed. CORS is added after custom middleware,
        so it appears first in the list. Custom middleware follows.
        """
        middleware_classes = [
            m.cls.__name__ for m in app.user_middleware
        ]
        # CORS is outermost (added last in app.py)
        assert middleware_classes[0] == "CORSMiddleware"
        # Then our custom middleware
        assert "RecoveryMiddleware" in middleware_classes
        assert "TimingMiddleware" in middleware_classes
        assert "CorrelationIDMiddleware" in middleware_classes
        assert "RequestIDMiddleware" in middleware_classes
        # Verify custom middleware order relative to each other
        # user_middleware stores in reverse execution order (last added = index 0 = outermost)
        recovery_idx = middleware_classes.index("RecoveryMiddleware")
        timing_idx = middleware_classes.index("TimingMiddleware")
        correlation_idx = middleware_classes.index("CorrelationIDMiddleware")
        request_idx = middleware_classes.index("RequestIDMiddleware")
        assert request_idx < correlation_idx < timing_idx < recovery_idx


class TestAppSettings:
    """Test that settings are stored on app.state."""

    def test_settings_on_app_state(self, app, settings):
        """Settings should be stored on app.state."""
        assert hasattr(app.state, "settings")
        assert app.state.settings is settings
