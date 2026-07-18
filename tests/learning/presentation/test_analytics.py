"""Tests for GET /analytics endpoint."""
from __future__ import annotations


class TestAnalyticsEndpoint:
    """Analytics endpoint test suite."""

    def test_analytics_returns_200(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200

    def test_analytics_response_schema(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "total_feedback",
            "approval_ratio",
            "total_signals",
            "signals_by_dimension",
            "average_approval_rate",
            "top_sources",
            "model_version",
        }
        assert required_fields.issubset(data.keys())

    def test_analytics_empty_state(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] == 0
        assert data["total_signals"] == 0

    def test_analytics_approval_ratio_in_range(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["approval_ratio"] <= 1.0

    def test_analytics_signals_by_dimension_is_dict(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["signals_by_dimension"], dict)

    def test_analytics_top_sources_is_list(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["top_sources"], list)

    def test_analytics_after_feedback_increments_count(self, client):
        # Record some feedback
        for i in range(3):
            client.post(
                "/api/v1/learning/feedback",
                json={
                    "topic_id": f"topic-analytics-{i}",
                    "decision": "APPROVED",
                    "source_name": "analytics_test_source",
                },
            )
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_feedback"] >= 3

    def test_analytics_model_version_is_string(self, client):
        response = client.get("/api/v1/learning/analytics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["model_version"], str)
