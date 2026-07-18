"""Tests for POST /feedback endpoint."""
from __future__ import annotations


class TestFeedbackEndpoint:
    """Feedback endpoint test suite."""

    def test_feedback_returns_200_with_valid_approved(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-001",
                "decision": "APPROVED",
                "source_name": "reuters",
                "title": "Test article",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "APPROVED"
        assert data["message"] == "Feedback recorded successfully"

    def test_feedback_returns_200_with_valid_rejected(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-002",
                "decision": "REJECTED",
                "reason": "Low quality content",
                "source_name": "reuters",
                "title": "Bad article",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "REJECTED"

    def test_feedback_response_schema(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-003",
                "decision": "APPROVED",
                "source_name": "bbc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        required_fields = {"feedback_id", "topic_id", "decision", "captured_at", "message"}
        assert required_fields.issubset(data.keys())

    def test_feedback_with_feature_snapshot(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-004",
                "decision": "APPROVED",
                "source_name": "reuters",
                "feature_snapshot": {
                    "base_score": 0.8,
                    "freshness_score": 0.7,
                    "keyword_bonus": 0.5,
                    "source_bonus": 0.6,
                    "topic_penalty": 0.1,
                    "confidence": 0.9,
                    "final_score": 0.75,
                },
            },
        )
        assert response.status_code == 200

    def test_feedback_missing_topic_id_returns_422(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "decision": "APPROVED",
                "source_name": "reuters",
            },
        )
        assert response.status_code == 422

    def test_feedback_invalid_decision_returns_422(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-005",
                "decision": "INVALID_DECISION",
                "source_name": "reuters",
            },
        )
        assert response.status_code == 422

    def test_feedback_feedback_id_is_string(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-006",
                "decision": "APPROVED",
                "source_name": "reuters",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["feedback_id"], str)
        assert len(data["feedback_id"]) > 0

    def test_feedback_captured_at_is_iso_format(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-007",
                "decision": "APPROVED",
                "source_name": "bbc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should be parseable as ISO format
        assert "T" in data["captured_at"]

    def test_feedback_immutability_multiple_submissions(self, client):
        # Submit two feedbacks for the same topic — both should succeed
        for i in range(2):
            response = client.post(
                "/api/v1/learning/feedback",
                json={
                    "topic_id": "topic-shared",
                    "decision": "APPROVED",
                    "source_name": "reuters",
                    "title": f"Article {i}",
                },
            )
            assert response.status_code == 200

    def test_feedback_auto_approved(self, client):
        response = client.post(
            "/api/v1/learning/feedback",
            json={
                "topic_id": "topic-auto",
                "decision": "AUTO_APPROVED",
                "source_name": "reuters",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "AUTO_APPROVED"
