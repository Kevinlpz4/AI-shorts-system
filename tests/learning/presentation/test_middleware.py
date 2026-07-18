"""Tests for Request ID, Correlation ID, and Timing middleware."""
from __future__ import annotations


class TestMiddleware:
    """Middleware test suite."""

    def test_request_id_header_present(self, client):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_correlation_id_header_present(self, client):
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers

    def test_timing_header_present(self, client):
        response = client.get("/health")
        assert "X-Response-Time" in response.headers

    def test_timing_header_format(self, client):
        response = client.get("/health")
        timing = response.headers["X-Response-Time"]
        assert timing.endswith("ms")
        # Should be parseable as a float
        value = timing.replace("ms", "").strip()
        assert float(value) >= 0.0

    def test_client_provided_request_id_preserved(self, client):
        custom_id = "test-request-id-12345"
        response = client.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["X-Request-ID"] == custom_id

    def test_client_provided_correlation_id_preserved(self, client):
        correlation_id = "corr-67890"
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": correlation_id},
        )
        assert response.headers["X-Correlation-ID"] == correlation_id

    def test_correlation_id_defaults_to_request_id(self, client):
        response = client.get("/health")
        # When no X-Correlation-ID is provided, it defaults to X-Request-ID
        assert response.headers["X-Correlation-ID"] == response.headers["X-Request-ID"]

    def test_request_id_is_uuid_format(self, client):
        response = client.get("/health")
        request_id = response.headers["X-Request-ID"]
        # UUID4 format: 8-4-4-4-12
        parts = request_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[4]) == 12
