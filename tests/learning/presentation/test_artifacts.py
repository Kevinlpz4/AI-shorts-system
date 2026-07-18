"""Tests for GET /artifacts endpoint."""
from __future__ import annotations


class TestArtifactsEndpoint:
    """Artifacts endpoint test suite."""

    def test_artifacts_returns_200(self, client):
        response = client.get("/api/v1/learning/artifacts")
        assert response.status_code == 200

    def test_artifacts_returns_list(self, client):
        response = client.get("/api/v1/learning/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_artifacts_empty_when_no_repository(self, client):
        # With artifact_repo=None, should return empty list
        response = client.get("/api/v1/learning/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_artifacts_with_type_filter(self, client):
        response = client.get(
            "/api/v1/learning/artifacts",
            params={"artifact_type": "DATASET"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_artifacts_with_invalid_type_filter(self, client):
        # Invalid type should still return 200 with empty list (no repo)
        response = client.get(
            "/api/v1/learning/artifacts",
            params={"artifact_type": "INVALID"},
        )
        assert response.status_code == 200

    def test_artifacts_empty_list_has_no_items(self, client):
        response = client.get("/api/v1/learning/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
