"""Tests for GET /knowledge endpoint."""
from __future__ import annotations


class TestKnowledgeEndpoint:
    """Knowledge endpoint test suite."""

    def test_knowledge_returns_200(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200

    def test_knowledge_response_schema(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "top_sources",
            "top_keywords",
            "top_categories",
            "top_topics",
            "active_signals_count",
            "knowledge_coverage",
            "model_version",
        }
        assert required_fields.issubset(data.keys())

    def test_knowledge_top_sources_is_list(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["top_sources"], list)

    def test_knowledge_top_keywords_is_list(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["top_keywords"], list)

    def test_knowledge_coverage_in_valid_range(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["knowledge_coverage"] <= 1.0

    def test_knowledge_active_signals_count_is_int(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["active_signals_count"], int)
        assert data["active_signals_count"] >= 0

    def test_knowledge_model_version_is_string(self, client):
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["model_version"], str)

    def test_knowledge_after_feedback_shows_source(self, client):
        # Record feedback to create a source
        client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-kw-1",
                "decision": "APPROVED",
                "source_name": "knowledge_test_source",
            },
        )
        response = client.get("/api/v1/learning/knowledge")
        assert response.status_code == 200
        data = response.json()
        source_names = [s["source_name"] for s in data["top_sources"]]
        assert "knowledge_test_source" in source_names
