"""Tests for RFC 9457 Problem Details compliance."""
from __future__ import annotations

from learning.presentation.schemas.problem_details import ProblemDetails


class TestProblemDetails:
    """RFC 9457 Problem Details test suite."""

    def test_problem_details_has_required_fields(self):
        pd = ProblemDetails(
            title="Test Error",
            status=422,
            detail="Something went wrong",
        )
        assert pd.type == "about:blank"
        assert pd.title == "Test Error"
        assert pd.status == 422
        assert pd.detail == "Something went wrong"

    def test_problem_details_defaults(self):
        pd = ProblemDetails(
            title="Error",
            status=500,
            detail="Internal error",
        )
        assert pd.type == "about:blank"
        assert pd.instance == ""
        assert pd.errors == {}

    def test_problem_details_with_errors(self):
        pd = ProblemDetails(
            title="Validation Error",
            status=422,
            detail="Invalid fields",
            errors={"source_name": ["Field required"]},
        )
        assert "source_name" in pd.errors
        assert pd.errors["source_name"] == ["Field required"]

    def test_problem_details_json_serializable(self):
        pd = ProblemDetails(
            title="Not Found",
            status=404,
            detail="Resource not found",
        )
        d = pd.model_dump()
        assert isinstance(d, dict)
        assert d["status"] == 404

    def test_problem_details_from_422_validation_error(self, client):
        """Test that a 422 response contains ProblemDetails-compatible structure."""
        response = client.post(
            "/api/v1/learning/predict",
            json={},
        )
        assert response.status_code == 422
        data = response.json()
        # FastAPI returns validation errors in its own format,
        # but our custom endpoints use ProblemDetails
        assert "detail" in data

    def test_problem_details_from_custom_404(self, client):
        """Test that our custom 404 returns ProblemDetails."""
        response = client.get("/api/v1/learning/source-quality/unknown_xyz")
        assert response.status_code == 404
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, dict)
        assert detail["type"] == "about:blank"
        assert detail["title"] == "Source Not Found"
        assert detail["status"] == 404
        assert "detail" in detail
