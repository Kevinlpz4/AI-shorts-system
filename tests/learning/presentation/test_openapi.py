"""Tests for OpenAPI schema generation and validation."""
from __future__ import annotations


class TestOpenAPI:
    """OpenAPI schema test suite."""

    def test_openapi_schema_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_is_valid_json(self, client):
        response = client.get("/openapi.json")
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    def test_openapi_schema_has_all_endpoints(self, client):
        response = client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]
        expected_endpoints = [
            "/health",
            "/ready",
            "/live",
            "/api/v1/learning/predict",
            "/api/v1/learning/explain/{article_id}",
            "/api/v1/learning/recommend",
            "/api/v1/learning/feedback",
            "/api/v1/learning/source-quality/{source}",
            "/api/v1/learning/knowledge",
            "/api/v1/learning/timeline",
            "/api/v1/learning/signals",
            "/api/v1/learning/datasets",
            "/api/v1/learning/datasets/{version}",
            "/api/v1/learning/datasets/export",
            "/api/v1/learning/artifacts",
            "/api/v1/learning/analytics",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Missing endpoint: {endpoint}"

    def test_openapi_info_correct(self, client):
        response = client.get("/openapi.json")
        data = response.json()
        assert data["info"]["title"] == "Learning Intelligence API"
        assert data["info"]["version"] == "1.0.0"

    def test_openapi_tags_defined(self, client):
        response = client.get("/openapi.json")
        data = response.json()
        assert "tags" in data
        tag_names = [t["name"] for t in data["tags"]]
        expected_tags = [
            "Health",
            "Prediction",
            "Explanation",
            "Recommendation",
            "Feedback",
            "Source Intelligence",
            "Knowledge",
            "Timeline",
            "Signals",
            "Datasets",
            "Artifacts",
            "Analytics",
        ]
        for tag in expected_tags:
            assert tag in tag_names, f"Missing tag: {tag}"
