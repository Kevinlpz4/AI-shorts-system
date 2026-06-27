"""
Tests para las Exceptions del dominio.
"""
import pytest
from domain.exceptions.base import DomainError
from domain.exceptions.ai import AIProviderError, QuotaExceededError, ProviderUnavailableError, RateLimitError
from domain.exceptions.content import ContentError, IdeaGenerationError, ScriptGenerationError
from domain.exceptions.media import TTSError, VideoRenderError
from domain.exceptions.publishing import PublishError, PlatformNotSupportedError
from domain.exceptions.trends import TrendNotFoundError, TrendSourceError


class TestDomainError:
    """Tests para DomainError base."""

    def test_has_message(self):
        err = DomainError("Algo salió mal")
        assert str(err) == "Algo salió mal"
        assert err.user_message == "Algo salió mal"

    def test_default_code(self):
        err = DomainError("test")
        assert err.code == "DOMAIN_ERROR"

    def test_default_status(self):
        err = DomainError("test")
        assert err.status_code == 500

    def test_default_log_level(self):
        err = DomainError("test")
        assert err.log_level == "error"

    def test_default_template(self):
        err = DomainError()
        assert "inesperado" in err.user_message

    def test_to_dict(self):
        err = DomainError("test detail")
        d = err.to_dict()
        assert d["error"] == "DOMAIN_ERROR"
        assert d["status_code"] == 500
        assert d["detail"] == "test detail"

    def test_error_with_kwargs(self):
        err = PlatformNotSupportedError(platform="twitter")
        assert "twitter" in err.detail


class TestAIExceptions:
    def test_ai_provider_error(self):
        err = AIProviderError("Error")
        assert err.code == "AI_PROVIDER_ERROR"
        assert err.status_code == 503

    def test_quota_exceeded(self):
        err = QuotaExceededError("Sin créditos")
        assert err.code == "QUOTA_EXCEEDED"
        assert err.status_code == 429

    def test_provider_unavailable(self):
        err = ProviderUnavailableError("Caído")
        assert err.code == "PROVIDER_UNAVAILABLE"
        assert err.status_code == 503

    def test_rate_limit(self):
        err = RateLimitError("Límite")
        assert err.code == "RATE_LIMIT_EXCEEDED"
        assert err.status_code == 429

    def test_ai_hierarchy(self):
        assert issubclass(QuotaExceededError, AIProviderError)
        assert issubclass(AIProviderError, DomainError)


class TestContentExceptions:
    def test_content_error(self):
        err = ContentError("Error")
        assert err.code == "CONTENT_ERROR"
        assert err.status_code == 422

    def test_idea_generation(self):
        err = IdeaGenerationError("falló")
        assert err.code == "IDEA_GENERATION_ERROR"

    def test_script_generation(self):
        err = ScriptGenerationError("falló")
        assert err.code == "SCRIPT_GENERATION_ERROR"

    def test_content_hierarchy(self):
        assert issubclass(IdeaGenerationError, ContentError)
        assert issubclass(ContentError, DomainError)


class TestMediaExceptions:
    def test_tts_error(self):
        err = TTSError("Error TTS")
        assert err.code == "TTS_ERROR"
        assert err.status_code == 502

    def test_video_render_error(self):
        err = VideoRenderError("Error")
        assert err.code == "VIDEO_RENDER_ERROR"
        assert err.status_code == 500

    def test_media_hierarchy(self):
        assert issubclass(TTSError, DomainError)
        assert issubclass(VideoRenderError, DomainError)


class TestPublishingExceptions:
    def test_publish_error(self):
        err = PublishError("Error")
        assert err.code == "PUBLISH_ERROR"
        assert err.status_code == 502

    def test_platform_not_supported(self):
        err = PlatformNotSupportedError(platform="twitter")
        assert err.code == "PLATFORM_NOT_SUPPORTED"
        assert err.status_code == 400
        assert isinstance(err, PublishError)


class TestTrendExceptions:
    def test_trend_not_found(self):
        err = TrendNotFoundError("No trends")
        assert err.code == "TREND_NOT_FOUND"
        assert err.status_code == 404

    def test_trend_source_error(self):
        err = TrendSourceError("API down")
        assert err.code == "TREND_SOURCE_ERROR"
        assert err.status_code == 502


class TestErrorHierarchy:
    def test_all_are_domain_errors(self):
        errors = [
            QuotaExceededError(""),
            ProviderUnavailableError(""),
            IdeaGenerationError(""),
            TTSError(""),
            VideoRenderError(""),
            PublishError(""),
            TrendNotFoundError(""),
            RateLimitError(""),
        ]
        for err in errors:
            assert isinstance(err, DomainError), f"{type(err).__name__} no hereda de DomainError"
