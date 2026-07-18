"""Tests for GET /timeline endpoint."""
from __future__ import annotations


class TestTimelineEndpoint:
    """Timeline endpoint test suite."""

    def test_timeline_returns_200_with_valid_params(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "source",
                "entity_id": "reuters",
                "metric_name": "approval_rate",
            },
        )
        assert response.status_code == 200

    def test_timeline_response_schema(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "source",
                "entity_id": "reuters",
            },
        )
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "entity_type",
            "entity_id",
            "metric_name",
            "snapshots",
            "trend",
        }
        assert required_fields.issubset(data.keys())

    def test_timeline_empty_when_no_data(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "source",
                "entity_id": "unknown_entity",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["snapshots"] == []

    def test_timeline_trend_is_valid_value(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "source",
                "entity_id": "reuters",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] in ("IMPROVING", "DECLINING", "STABLE", "INSUFFICIENT_DATA")

    def test_timeline_entity_params_echoed_back(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "keyword",
                "entity_id": "python",
                "metric_name": "effectiveness",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "keyword"
        assert data["entity_id"] == "python"
        assert data["metric_name"] == "effectiveness"

    def test_timeline_missing_entity_type_returns_422(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={"entity_id": "reuters"},
        )
        assert response.status_code == 422

    def test_timeline_missing_entity_id_returns_422(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={"entity_type": "source"},
        )
        assert response.status_code == 422

    def test_timeline_snapshots_is_list(self, client):
        response = client.get(
            "/api/v1/learning/timeline",
            params={
                "entity_type": "source",
                "entity_id": "reuters",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["snapshots"], list)
