"""
Tests para ErrorMapper de la capa de aplicación.
"""
import pytest
import logging
from application.error_mapper import ErrorMapper
from domain.exceptions.ai import QuotaExceededError, ProviderUnavailableError, RateLimitError
from domain.exceptions.content import IdeaGenerationError, ScriptGenerationError
from domain.exceptions.media import TTSError, VideoRenderError
from domain.exceptions.publishing import PublishError, PlatformNotSupportedError
from domain.exceptions.trends import TrendNotFoundError


class TestErrorMapper:
    """Tests para ErrorMapper — mapeo de DomainError a respuestas."""

    def test_map_ai_provider_error(self):
        err = QuotaExceededError("Sin créditos")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.WARNING
        assert status == 429
        assert "créditos" in msg

    def test_map_provider_unavailable(self):
        err = ProviderUnavailableError("Caído")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.WARNING
        assert status == 503

    def test_map_rate_limit(self):
        err = RateLimitError("Límite")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.WARNING
        assert status == 429

    def test_map_idea_generation(self):
        err = IdeaGenerationError("falló")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR
        assert "generar la idea" in msg

    def test_map_script_generation(self):
        err = ScriptGenerationError("falló")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR

    def test_map_tts_error(self):
        err = TTSError("Error TTS")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.WARNING
        assert status == 502
        assert "audio" in msg

    def test_map_video_render(self):
        err = VideoRenderError("Error")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR
        assert status == 500

    def test_map_trend_not_found(self):
        err = TrendNotFoundError("No trends")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.INFO
        assert status == 404

    def test_map_publish_error(self):
        err = PublishError("Error")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR
        assert status == 502

    def test_map_platform_not_supported(self):
        err = PlatformNotSupportedError(platform="twitter")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR
        assert status == 400

    def test_map_unknown_error_falls_back(self):
        """Errores no registrados deben tener fallback."""
        from domain.exceptions.base import DomainError
        class UnknownError(DomainError):
            code = "UNKNOWN"

        err = UnknownError("test")
        level, msg, status = ErrorMapper.map(err)
        assert level == logging.ERROR
        assert status == 500
        assert "inesperado" in msg

    def test_map_is_idempotent(self):
        err = QuotaExceededError("test")
        first = ErrorMapper.map(err)
        second = ErrorMapper.map(err)
        assert first == second

    def test_to_response(self):
        err = QuotaExceededError("Sin créditos")
        resp = ErrorMapper.to_response(err)
        assert resp["error"] == "QUOTA_EXCEEDED"
        assert resp["status_code"] == 429
        assert "level" in resp

    def test_should_retry_rate_limit(self):
        assert ErrorMapper.should_retry(RateLimitError("")) is True
        assert ErrorMapper.should_retry(ProviderUnavailableError("")) is True
        assert ErrorMapper.should_retry(TTSError("")) is False

    def test_should_fallback(self):
        assert ErrorMapper.should_fallback(QuotaExceededError("")) is True
        assert ErrorMapper.should_fallback(ProviderUnavailableError("")) is True
        assert ErrorMapper.should_fallback(TTSError("")) is True
        assert ErrorMapper.should_fallback(ScriptGenerationError("")) is False
