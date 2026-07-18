"""Tests for GET /signals endpoint."""
from __future__ import annotations


class TestSignalsEndpoint:
    """Signals endpoint test suite."""

    def test_signals_returns_200(self, client):
        response = client.get("/api/v1/learning/signals")
        assert response.status_code == 200

    def test_signals_returns_list(self, client):
        response = client.get("/api/v1/learning/signals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_signals_response_schema(self, client):
        response = client.get("/api/v1/learning/signals")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            signal = data[0]
            required_fields = {
                "signal_type",
                "dimension",
                "strength",
                "decay_factor",
                "sample_size",
                "approval_rate",
                "window_start",
                "window_end",
                "last_updated",
            }
            assert required_fields.issubset(signal.keys())

    def test_signals_filter_by_type(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={"signal_type": "KEYWORD"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for signal in data:
            assert signal["signal_type"] == "KEYWORD"

    def test_signals_filter_by_min_strength(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={"min_strength": 0.5},
        )
        assert response.status_code == 200
        data = response.json()
        for signal in data:
            assert signal["strength"] >= 0.5

    def test_signals_combined_filters(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={
                "signal_type": "SOURCE",
                "min_strength": 0.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        for signal in data:
            assert signal["signal_type"] == "SOURCE"
            assert signal["strength"] >= 0.0

    def test_signals_strength_in_valid_range(self, client):
        response = client.get("/api/v1/learning/signals")
        assert response.status_code == 200
        data = response.json()
        for signal in data:
            assert 0.0 <= signal["strength"] <= 1.0
            assert 0.0 <= signal["decay_factor"] <= 1.0

    def test_signals_empty_when_no_match(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={"signal_type": "NONEXISTENT"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_signals_invalid_min_strength_returns_422(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={"min_strength": 1.5},
        )
        assert response.status_code == 422

    def test_signals_invalid_min_strength_negative_returns_422(self, client):
        response = client.get(
            "/api/v1/learning/signals",
            params={"min_strength": -0.1},
        )
        assert response.status_code == 422
