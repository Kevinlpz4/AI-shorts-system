"""
Tests for OpenAPI Schema Configuration (REQ-F7).

Validates:
- OpenAPI schema has correct title and version
- OpenAPI schema includes /health/live and /health/ready paths
"""

from __future__ import annotations

import pytest


class TestOpenAPISchema:
    """Test the auto-generated OpenAPI schema."""

    @pytest.mark.anyio
    async def test_openapi_schema_has_info(self, client):
        """OpenAPI schema should have correct title and version."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"].startswith("AI Shorts System")
        assert schema["info"]["version"] == "1.0.0"

    @pytest.mark.anyio
    async def test_openapi_schema_has_health_tags(self, client):
        """OpenAPI schema should include health endpoints."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "/health/live" in schema["paths"]
        assert "/health/ready" in schema["paths"]
