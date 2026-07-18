"""Tests for POST /predict endpoint."""
from __future__ import annotations


class TestPredictionEndpoint:
    """Prediction endpoint test suite."""

    def test_predict_returns_200_with_valid_request(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "reuters"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert "score" in data
        assert "confidence" in data
        assert "explanation" in data
        assert "model_version" in data

    def test_predict_recommendation_values(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "reuters"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] in ("APPROVE", "REJECT", "MANUAL_REVIEW")

    def test_predict_score_in_valid_range(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "reuters"},
        )
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["score"] <= 1.0

    def test_predict_confidence_in_valid_range(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "reuters"},
        )
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_with_features(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={
                "source_name": "techcrunch",
                "features": {"final_score": 0.75},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
        assert isinstance(data["explanation"], str)

    def test_predict_with_empty_source_name_returns_422(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": ""},
        )
        assert response.status_code == 422

    def test_predict_with_missing_source_name_returns_422(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={},
        )
        assert response.status_code == 422

    def test_predict_response_schema_matches_model(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "bbc"},
        )
        assert response.status_code == 200
        data = response.json()
        required_fields = {
            "recommendation",
            "score",
            "confidence",
            "explanation",
            "model_version",
        }
        assert required_fields.issubset(data.keys())

    def test_predict_with_title(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={
                "source_name": "reuters",
                "title": "Breaking news about AI",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] in ("APPROVE", "REJECT", "MANUAL_REVIEW")

    def test_predict_unknown_source_returns_valid_response(self, client):
        response = client.post(
            "/api/v1/learning/predict",
            json={"source_name": "unknown_source_xyz"},
        )
        # Unknown sources should still return a valid prediction (with 0 probability)
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["score"] <= 1.0
