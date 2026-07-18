"""Tests for health endpoints: /health, /ready, /live."""
from __future__ import annotations


class TestHealthEndpoints:
    """Health endpoint test suite."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_schema(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "learning-intelligence-api"

    def test_ready_returns_200(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_live_returns_200(self, client):
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_endpoints_no_auth(self, client):
        for path in ("/health", "/ready", "/live"):
            response = client.get(path)
            assert response.status_code == 200
