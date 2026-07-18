"""Tests for GET /datasets, GET /datasets/{version}, POST /datasets/export."""
from __future__ import annotations


class TestDatasetsEndpoint:
    """Datasets endpoint test suite."""

    def test_list_datasets_returns_200(self, client):
        response = client.get("/api/v1/learning/datasets")
        assert response.status_code == 200

    def test_list_datasets_returns_list(self, client):
        response = client.get("/api/v1/learning/datasets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_datasets_empty_when_no_repository(self, client):
        # With dataset_repository=None, should return empty list
        response = client.get("/api/v1/learning/datasets")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_dataset_not_found(self, client):
        response = client.get("/api/v1/learning/datasets/nonexistent-v1")
        assert response.status_code == 404

    def test_get_dataset_404_has_problem_details(self, client):
        response = client.get("/api/v1/learning/datasets/missing-v1")
        assert response.status_code == 404
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, dict)
        assert detail["status"] == 404

    def test_export_dataset_returns_200(self, client):
        response = client.post(
            "/api/v1/learning/datasets/export",
            json={"format": "JSONL"},
        )
        assert response.status_code == 200

    def test_export_dataset_response_schema(self, client):
        response = client.post(
            "/api/v1/learning/datasets/export",
            json={"format": "CSV"},
        )
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "dataset_id",
            "version",
            "created_at",
            "algorithm_version",
            "record_count",
            "approved_count",
            "rejected_count",
            "export_format",
            "checksum",
            "description",
            "status",
        }
        assert required_fields.issubset(data.keys())

    def test_export_dataset_format_reflected(self, client):
        response = client.post(
            "/api/v1/learning/datasets/export",
            json={"format": "CSV"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["export_format"] == "CSV"

    def test_export_dataset_status_is_pending(self, client):
        response = client.post(
            "/api/v1/learning/datasets/export",
            json={"format": "JSONL"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"

    def test_export_invalid_format_returns_422(self, client):
        response = client.post(
            "/api/v1/learning/datasets/export",
            json={"format": "XML"},
        )
        assert response.status_code == 422
