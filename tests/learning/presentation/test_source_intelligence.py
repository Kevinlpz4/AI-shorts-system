"""Tests for GET /source-quality/{source} endpoint."""
from __future__ import annotations


class TestSourceIntelligenceEndpoint:
    """Source Intelligence endpoint test suite."""

    def test_source_quality_unknown_source_returns_404(self, client):
        response = client.get("/api/v1/learning/source-quality/nonexistent_source_xyz")
        assert response.status_code == 404

    def test_source_quality_404_has_problem_details(self, client):
        response = client.get("/api/v1/learning/source-quality/unknown")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert isinstance(detail, dict)
        assert detail["status"] == 404
        assert detail["title"] == "Source Not Found"

    def test_source_quality_after_feedback(self, client):
        # First record feedback for a source
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-1",
                "decision": "APPROVED",
                "source_name": "tested_source",
            },
        )
        # Then query source quality
        response = client.get("/api/v1/learning/source-quality/tested_source")
        assert response.status_code == 200
        data = response.json()
        assert data["source_name"] == "tested_source"

    def test_source_quality_response_schema(self, client):
        # Record feedback first to create source
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-2",
                "decision": "APPROVED",
                "source_name": "schema_test_source",
            },
        )
        response = client.get("/api/v1/learning/source-quality/schema_test_source")
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "source_name",
            "approval_rate",
            "total_decisions",
            "approved_count",
            "rejected_count",
            "confidence",
            "trend",
            "keywords",
        }
        assert required_fields.issubset(data.keys())

    def test_source_quality_approval_rate_in_range(self, client):
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-3",
                "decision": "APPROVED",
                "source_name": "rate_test_source",
            },
        )
        response = client.get("/api/v1/learning/source-quality/rate_test_source")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["approval_rate"] <= 1.0

    def test_source_quality_confidence_in_range(self, client):
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-4",
                "decision": "APPROVED",
                "source_name": "conf_test_source",
            },
        )
        response = client.get("/api/v1/learning/source-quality/conf_test_source")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_source_quality_keywords_is_list(self, client):
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-5",
                "decision": "APPROVED",
                "source_name": "kw_test_source",
            },
        )
        response = client.get("/api/v1/learning/source-quality/kw_test_source")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["keywords"], list)

    def test_source_quality_trend_is_string(self, client):
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-sq-6",
                "decision": "REJECTED",
                "reason": "Bad quality",
                "source_name": "trend_test_source",
            },
        )
        response = client.get("/api/v1/learning/source-quality/trend_test_source")
        assert response.status_code == 200
        data = response.json()
        assert data["trend"] in ("IMPROVING", "DECLINING", "STABLE")

    def test_source_quality_total_decisions_matches_feedback(self, client):
        # Record 3 feedbacks
        for i in range(3):
            client.post(
                "/api/v1/learning/feedback",
                json={
                    "topic_id": f"topic-count-{i}",
                    "decision": "APPROVED",
                    "source_name": "count_test_source",
                },
            )
        response = client.get("/api/v1/learning/source-quality/count_test_source")
        assert response.status_code == 200
        data = response.json()
        assert data["total_decisions"] >= 3
