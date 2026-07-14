"""
Tests for Exception Handlers and Error Logging (REQ-F9).

Validates:
- Problem Details responses have correct content-type (application/problem+json)
- 5xx errors log stacktrace (exc_info=True)
- 4xx errors do NOT log stacktrace
- PersistenceError → 503 + Problem Details
- InfrastructureError → 503 + Problem Details
- FoundationError → 500 + Problem Details
- Generic Exception → 500 + Problem Details
- Error log includes path and method fields

Uses test routes that raise specific exceptions to exercise the
registered exception handlers in ``exceptions.py``.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from fastapi import APIRouter

from foundation.errors.base import FoundationError, InfrastructureError
from ingestion.infrastructure.persistence.exceptions import PersistenceError

# ── Test router with endpoints that raise specific exceptions ──

_exc_router = APIRouter()


@_exc_router.get("/test/persistence-error")
async def raise_persistence_error():
    """Raise a PersistenceError (→ 503)."""
    raise PersistenceError("Database connection lost")


@_exc_router.get("/test/infrastructure-error")
async def raise_infrastructure_error():
    """Raise an InfrastructureError (→ 503)."""
    raise InfrastructureError("External service timeout")


@_exc_router.get("/test/foundation-error")
async def raise_foundation_error():
    """Raise a FoundationError (→ 500)."""
    raise FoundationError("Something went wrong")


@_exc_router.get("/test/generic-exception")
async def raise_generic_exception():
    """Raise a generic Exception (→ 500)."""
    raise RuntimeError("Unexpected failure")


@_exc_router.get("/test/ok")
async def test_ok():
    """Successful endpoint for 4xx comparison."""
    return {"message": "ok"}


@pytest.fixture(autouse=True)
def _register_exc_routes(app):
    """Register exception-testing routes on the app."""
    app.include_router(_exc_router)


# ══════════════════════════════════════════════════════════════════════════════
# Content-Type Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestProblemDetailsContentType:
    """Test that all error responses use application/problem+json."""

    @pytest.mark.anyio
    async def test_persistence_error_content_type(self, client):
        """PersistenceError response should have problem+json content type."""
        response = await client.get("/test/persistence-error")
        assert response.headers["content-type"] == "application/problem+json"

    @pytest.mark.anyio
    async def test_infrastructure_error_content_type(self, client):
        """InfrastructureError response should have problem+json content type."""
        response = await client.get("/test/infrastructure-error")
        assert response.headers["content-type"] == "application/problem+json"

    @pytest.mark.anyio
    async def test_foundation_error_content_type(self, client):
        """FoundationError response should have problem+json content type."""
        response = await client.get("/test/foundation-error")
        assert response.headers["content-type"] == "application/problem+json"

    @pytest.mark.anyio
    async def test_generic_exception_content_type(self, client):
        """Generic Exception response should have problem+json content type."""
        response = await client.get("/test/generic-exception")
        assert response.headers["content-type"] == "application/problem+json"


# ══════════════════════════════════════════════════════════════════════════════
# Exception → HTTP Status Mapping Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestExceptionStatusMapping:
    """Test that each exception type maps to the correct HTTP status."""

    @pytest.mark.anyio
    async def test_persistence_error_returns_503(self, client):
        """PersistenceError should map to 503 Service Unavailable."""
        response = await client.get("/test/persistence-error")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == 503
        assert body["title"] == "Service Unavailable"
        assert "persistence" in body["detail"].lower()

    @pytest.mark.anyio
    async def test_infrastructure_error_returns_503(self, client):
        """InfrastructureError should map to 503 Service Unavailable."""
        response = await client.get("/test/infrastructure-error")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == 503
        assert body["title"] == "Service Unavailable"
        assert "infrastructure" in body["detail"].lower()

    @pytest.mark.anyio
    async def test_foundation_error_returns_500(self, client):
        """FoundationError should map to 500 Internal Server Error."""
        response = await client.get("/test/foundation-error")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == 500
        assert body["title"] == "Internal Server Error"

    @pytest.mark.anyio
    async def test_generic_exception_returns_500(self, client):
        """Generic Exception should map to 500 Internal Server Error."""
        response = await client.get("/test/generic-exception")
        assert response.status_code == 500
        body = response.json()
        assert body["status"] == 500
        assert body["title"] == "Internal Server Error"


# ══════════════════════════════════════════════════════════════════════════════
# Problem Details Structure Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestProblemDetailsStructure:
    """Test that Problem Details responses have all required RFC 9457 fields."""

    @pytest.mark.anyio
    async def test_error_response_has_type_field(self, client):
        """Problem Details should include 'type' field."""
        response = await client.get("/test/persistence-error")
        body = response.json()
        assert "type" in body
        assert body["type"].startswith("https://")

    @pytest.mark.anyio
    async def test_error_response_has_title_field(self, client):
        """Problem Details should include 'title' field."""
        response = await client.get("/test/generic-exception")
        body = response.json()
        assert "title" in body
        assert isinstance(body["title"], str)
        assert len(body["title"]) > 0

    @pytest.mark.anyio
    async def test_error_response_has_status_field(self, client):
        """Problem Details should include 'status' field matching HTTP status."""
        response = await client.get("/test/persistence-error")
        body = response.json()
        assert "status" in body
        assert body["status"] == response.status_code

    @pytest.mark.anyio
    async def test_error_response_has_detail_field(self, client):
        """Problem Details should include 'detail' field."""
        response = await client.get("/test/infrastructure-error")
        body = response.json()
        assert "detail" in body
        assert isinstance(body["detail"], str)

    @pytest.mark.anyio
    async def test_error_response_has_instance_field(self, client):
        """Problem Details should include 'instance' field with request path."""
        response = await client.get("/test/foundation-error")
        body = response.json()
        assert "instance" in body
        assert "/test/foundation-error" in body["instance"]


# ══════════════════════════════════════════════════════════════════════════════
# 5xx Stacktrace Logging Tests
# ══════════════════════════════════════════════════════════════════════════════


class Test5xxLogging:
    """Test that 5xx errors log stacktrace (exc_info=True)."""

    @pytest.mark.anyio
    async def test_persistence_error_logs_exc_info(self, client, caplog):
        """PersistenceError handler should log with exc_info=True."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            response = await client.get("/test/persistence-error")
        assert response.status_code == 503
        # Check that a log record with exc_info was produced
        exc_records = [r for r in caplog.records if r.exc_info is not None]
        assert len(exc_records) >= 1, (
            "Expected at least one log record with exc_info for PersistenceError"
        )

    @pytest.mark.anyio
    async def test_infrastructure_error_logs_exc_info(self, client, caplog):
        """InfrastructureError handler should log with exc_info=True."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            response = await client.get("/test/infrastructure-error")
        assert response.status_code == 503
        exc_records = [r for r in caplog.records if r.exc_info is not None]
        assert len(exc_records) >= 1, (
            "Expected at least one log record with exc_info for InfrastructureError"
        )

    @pytest.mark.anyio
    async def test_foundation_error_logs_exc_info(self, client, caplog):
        """FoundationError handler should log with exc_info=True."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            response = await client.get("/test/foundation-error")
        assert response.status_code == 500
        exc_records = [r for r in caplog.records if r.exc_info is not None]
        assert len(exc_records) >= 1, (
            "Expected at least one log record with exc_info for FoundationError"
        )

    @pytest.mark.anyio
    async def test_generic_exception_logs_exc_info(self, client, caplog):
        """Generic Exception handler should log with exc_info=True."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            response = await client.get("/test/generic-exception")
        assert response.status_code == 500
        exc_records = [r for r in caplog.records if r.exc_info is not None]
        assert len(exc_records) >= 1, (
            "Expected at least one log record with exc_info for generic Exception"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4xx Error Logging Tests (no stacktrace)
# ══════════════════════════════════════════════════════════════════════════════


class Test4xxLogging:
    """Test that 4xx errors do NOT log stacktrace."""

    @pytest.mark.anyio
    async def test_404_does_not_log_exc_info(self, client, caplog):
        """Request to non-existent path should not produce exc_info logs."""
        with caplog.at_level(logging.WARNING, logger="ingestion.presentation.exceptions"):
            response = await client.get("/nonexistent-path-404")
        # FastAPI returns 404 for unknown routes
        assert response.status_code == 404
        exc_records = [r for r in caplog.records if r.exc_info is not None]
        assert len(exc_records) == 0, (
            "4xx errors should NOT log stacktrace (exc_info)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Log Extra Fields Tests (path, method)
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorLogExtraFields:
    """Test that error logs include path and method fields."""

    @pytest.mark.anyio
    async def test_persistence_error_log_includes_path_and_method(self, client, caplog):
        """PersistenceError log should include path and method extra fields."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            await client.get("/test/persistence-error")
        # Find the log record from exception handler
        handler_records = [
            r for r in caplog.records
            if "Persistence error" in r.getMessage()
        ]
        assert len(handler_records) >= 1
        record = handler_records[0]
        assert getattr(record, "path", None) == "/test/persistence-error"
        assert getattr(record, "method", None) == "GET"

    @pytest.mark.anyio
    async def test_generic_exception_log_includes_path_and_method(self, client, caplog):
        """Generic Exception log should include path and method extra fields."""
        with caplog.at_level(logging.ERROR, logger="ingestion.presentation.exceptions"):
            await client.get("/test/generic-exception")
        handler_records = [
            r for r in caplog.records
            if "Unhandled exception" in r.getMessage()
        ]
        assert len(handler_records) >= 1
        record = handler_records[0]
        assert getattr(record, "path", None) == "/test/generic-exception"
        assert getattr(record, "method", None) == "GET"
