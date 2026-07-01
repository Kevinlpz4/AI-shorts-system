"""
Tests para DTOs de la capa de aplicación.
"""
import pytest
from application.dtos.requests import GenerateContentRequest, EvaluateRequest, TrendRequest
from application.dtos.responses import ContentResult, EvaluationResponse


class TestGenerateContentRequest:
    def test_defaults(self):
        req = GenerateContentRequest()
        assert req.niche is None
        assert req.platform == "youtube"
        assert req.count == 1
        assert req.duration == 45
        assert req.tone == "educational"

    def test_custom_values(self):
        req = GenerateContentRequest(
            niche="tech",
            platform="tiktok",
            count=3,
            duration=60,
            tone="humor",
        )
        assert req.niche == "tech"
        assert req.platform == "tiktok"
        assert req.count == 3
        assert req.duration == 60

    def test_trend_sources_default(self):
        req = GenerateContentRequest()
        assert "news" in req.trend_sources


class TestEvaluateRequest:
    def test_defaults(self):
        req = EvaluateRequest()
        assert req.content_type == "idea"
        assert req.content_id == ""
        assert req.optimize is True

    def test_custom(self):
        req = EvaluateRequest(content_type="script", content_id="abc", optimize=False)
        assert req.content_type == "script"
        assert req.optimize is False


class TestTrendRequest:
    def test_defaults(self):
        req = TrendRequest()
        assert req.niche is None
        assert req.limit == 20

    def test_custom(self):
        req = TrendRequest(niche="tech", limit=5)
        assert req.niche == "tech"
        assert req.limit == 5


class TestContentResult:
    def test_ok(self):
        r = ContentResult.ok(data={"id": 1}, message="Todo bien")
        assert r.success is True
        assert r.data == {"id": 1}
        assert r.status_code == 200

    def test_fallback(self):
        r = ContentResult.fallback(message="Usando fallback")
        assert r.success is True
        assert r.status_code == 200

    def test_error(self):
        r = ContentResult.error("Algo falló", code="ERR", status=500)
        assert r.success is False
        assert r.message == "Algo falló"
        assert r.error_code == "ERR"
        assert r.status_code == 500

    def test_to_dict(self):
        r = ContentResult.ok(data={"key": "val"}, message="OK")
        d = r.to_dict()
        assert d["success"] is True
        assert d["data"] == {"key": "val"}
        assert d["status_code"] == 200


class TestEvaluationResponse:
    def test_create(self):
        r = EvaluationResponse(
            score=8.5,
            classification="excelente",
            criteria={"curiosidad": 8.0},
            recommendations=["N/A"],
            was_optimized=True,
        )
        assert r.score == 8.5
        assert r.was_optimized is True
