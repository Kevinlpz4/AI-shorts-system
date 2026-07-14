"""
Tests for Exception Handlers and Error Mappers (REQ-F5).

Validates:
- map_error_code_to_status maps domain codes to correct HTTP statuses
- map_error_code_to_status maps application codes to correct HTTP statuses
- map_error_code_to_status returns 500 for unknown codes
- PersistenceError exception handler returns 503 Problem Details
- FoundationError exception handler returns 500 Problem Details

Tests both the mapper function directly and the exception handlers via
a test router that raises specific exceptions.
"""

from __future__ import annotations

import pytest
from fastapi import APIRouter

from foundation.errors import FoundationError
from ingestion.infrastructure.persistence.exceptions import PersistenceError
from ingestion.presentation.exceptions import map_error_code_to_status

# ── Test router to trigger exception handlers ──

_exception_test_router = APIRouter()


@_exception_test_router.get("/test/persistence-error")
async def raise_persistence_error():
    """Endpoint that raises PersistenceError (should → 503)."""
    raise PersistenceError("DB connection lost")


@_exception_test_router.get("/test/foundation-error")
async def raise_foundation_error():
    """Endpoint that raises FoundationError (should → 500)."""
    raise FoundationError("Something went wrong")


@_exception_test_router.get("/test/generic-error")
async def raise_generic_error():
    """Endpoint that raises generic Exception (should → 500)."""
    raise RuntimeError("Unexpected failure")


@pytest.fixture(autouse=True)
def _register_exception_test_routes(app):
    """Register test routes on the app for exception handler tests."""
    app.include_router(_exception_test_router)


# ── Tests: map_error_code_to_status ──


class TestErrorCodeMapper:
    """Test map_error_code_to_status direct mapping logic."""

    def test_domain_not_found_404(self):
        """NEWS_SOURCE_NOT_FOUND should map to 404."""
        assert map_error_code_to_status("NEWS_SOURCE_NOT_FOUND") == 404

    def test_duplicate_409(self):
        """DUPLICATE_NEWS_SOURCE should map to 409."""
        assert map_error_code_to_status("DUPLICATE_NEWS_SOURCE") == 409

    def test_invalid_input_422(self):
        """INVALID_SOURCE_URL should map to 422."""
        assert map_error_code_to_status("INVALID_SOURCE_URL") == 422

    def test_application_code_422(self):
        """COMMAND_INVALID (application code) should map to 422."""
        assert map_error_code_to_status("COMMAND_INVALID") == 422

    def test_application_code_404(self):
        """RESOURCE_NOT_FOUND (application code) should map to 404."""
        assert map_error_code_to_status("RESOURCE_NOT_FOUND") == 404

    def test_unknown_error_500(self):
        """Unknown error codes should default to 500."""
        assert map_error_code_to_status("UNKNOWN_CODE") == 500


# ── Tests: Exception Handlers via HTTP ──


class TestPersistenceExceptionHandler:
    """Test PersistenceError → 503 exception handler."""

    @pytest.mark.anyio
    async def test_persistence_error_503(self, client):
        """PersistenceError should return 503 Problem Details."""
        response = await client.get("/test/persistence-error")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == 503
        assert body["title"] == "Service Unavailable"
        assert "service-unavailable" in body["type"]

    @pytest.mark.anyio
    async def test_persistence_error_content_type(self, client):
        """PersistenceError response should have problem+json content type."""
        response = await client.get("/test/persistence-error")
        assert response.headers["content-type"] == "application/problem+json"


class TestFoundationExceptionHandler:
    """Test FoundationError → 500 exception handler."""

    @pytest.mark.anyio
    async def test_foundation_error_500(self, client):
        """FoundationError should return 500 Problem Details."""
        response = await client.get("/test/foundation-error")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == 500
        assert body["title"] == "Internal Server Error"
        assert "internal-error" in body["type"]


class TestGenericExceptionHandler:
    """Test generic Exception → 500 exception handler."""

    @pytest.mark.anyio
    async def test_generic_error_500(self, client):
        """Unhandled exceptions should return 500 Problem Details."""
        response = await client.get("/test/generic-error")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == 500
        assert body["title"] == "Internal Server Error"
