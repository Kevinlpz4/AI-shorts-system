"""Tests for GET /explain/{article_id} endpoint."""
from __future__ import annotations


class TestExplanationEndpoint:
    """Explanation endpoint test suite."""

    def test_explain_returns_200_for_valid_source(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert "source_name" in data
        assert "final_score" in data

    def test_explain_response_schema(self, client):
        response = client.get("/api/v1/learning/explain/bbc")
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "source_name",
            "base_score",
            "freshness_score",
            "keyword_bonus",
            "source_bonus",
            "topic_penalty",
            "confidence",
            "final_score",
            "model_version",
            "active_signals",
            "positive_factors",
            "negative_factors",
        }
        assert required_fields.issubset(data.keys())

    def test_explain_source_name_matches_path_param(self, client):
        response = client.get("/api/v1/learning/explain/techcrunch")
        assert response.status_code == 200
        data = response.json()
        assert data["source_name"] == "techcrunch"

    def test_explain_active_signals_is_list(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["active_signals"], list)

    def test_explain_positive_negative_factors_are_lists(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["positive_factors"], list)
        assert isinstance(data["negative_factors"], list)

    def test_explain_final_score_in_valid_range(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["final_score"] <= 1.0

    def test_explain_confidence_in_valid_range(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_explain_unknown_source_returns_valid_response(self, client):
        # Unknown source should still produce a response with default values
        response = client.get("/api/v1/learning/explain/unknown_source")
        assert response.status_code == 200
        data = response.json()
        assert data["source_name"] == "unknown_source"
        assert 0.0 <= data["final_score"] <= 1.0

    def test_explain_model_version_is_string(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["model_version"], str)

    def test_explain_scores_are_floats(self, client):
        response = client.get("/api/v1/learning/explain/reuters")
        assert response.status_code == 200
        data = response.json()
        for field in ("base_score", "freshness_score", "keyword_bonus",
                      "source_bonus", "topic_penalty", "confidence", "final_score"):
            assert isinstance(data[field], float)
