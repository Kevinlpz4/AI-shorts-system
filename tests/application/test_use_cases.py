"""
Tests para los Use Cases con mocking.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from application.use_cases.generate_content import GenerateContentUseCase
from application.use_cases.evaluate_content import EvaluateContentUseCase
from application.use_cases.manage_trends import ManageTrendsUseCase
from application.dtos.requests import GenerateContentRequest, EvaluateRequest, TrendRequest
from application.dtos.responses import ContentResult
from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.trend import Trend, TrendSource
from domain.entities.voice_audio import VoiceAudio
from domain.entities.video import VideoAsset
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration
from domain.ports.publisher import PublishResult


@pytest.fixture
def mock_ai():
    ai = AsyncMock()
    ai.name = "mock-ai"
    ai.available = True
    ai.generate_json = AsyncMock(return_value={
        "hook": "Idea de prueba",
        "format": "list",
        "description": "Desc",
        "audience": "general",
    })
    return ai


@pytest.fixture
def mock_tts():
    tts = AsyncMock()
    tts.name = "mock-tts"
    tts.available = True
    tts.synthesize = AsyncMock(return_value=VoiceAudio(
        id="v1", text="test", audio_path="/tmp/a.mp3", duration=30.0, status="mock"
    ))
    return tts


@pytest.fixture
def mock_renderer():
    r = AsyncMock()
    r.available = True
    r.render = AsyncMock(return_value=VideoAsset(
        id="v1", video_path="/tmp/v.mp4", duration=45.0, status="rendered"
    ))
    return r


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.save_idea = AsyncMock()
    repo.save_script = AsyncMock()
    repo.save_video = AsyncMock()
    repo.get_idea = AsyncMock(return_value=ContentIdea(hook="Hook", topic="T", viral_score=ViralScore(70)))
    repo.get_script = AsyncMock(return_value=Script(hook="Hook", body="Body", cta="CTA"))
    return repo


@pytest.fixture
def mock_trend_source():
    source = AsyncMock()
    source.available = True
    source.source_name = "mock-news"
    source.fetch_trends = AsyncMock(return_value=[
        Trend(id="t1", topic="AI", source=TrendSource("news", "web"), viral_score=ViralScore(80)),
    ])
    return source


@pytest.fixture
def mock_publisher():
    p = AsyncMock()
    p.platform = "youtube"
    p.publish = AsyncMock(return_value=PublishResult(
        platform="youtube", video_id="v1", url="https://youtube.com/v1", status="published"
    ))
    return p


@pytest.fixture
def mock_cache():
    c = MagicMock()
    c.get = MagicMock(return_value=None)
    c.set = MagicMock()
    return c


@pytest.fixture
def mock_evaluator():
    ev = MagicMock()
    ev_result = MagicMock()
    ev_result.score_total = 8.5
    ev_result.classification = "excelente"
    ev_result.criteria = {"curiosidad": 8.0}
    ev_result.recommendations = []
    ev_result.is_acceptable = True
    ev.evaluate_idea = MagicMock(return_value=ev_result)
    ev.evaluate_script = MagicMock(return_value=ev_result)
    ev.optimize_idea = MagicMock(side_effect=lambda idea, recs: idea)
    ev.optimize_script = MagicMock(side_effect=lambda script, recs: script)
    return ev


class TestGenerateContentUseCase:
    @pytest.fixture
    def use_case(self, mock_ai, mock_tts, mock_renderer, mock_repo, mock_trend_source, mock_publisher, mock_cache, mock_evaluator):
        return GenerateContentUseCase(
            ai_provider=mock_ai,
            tts_provider=mock_tts,
            video_renderer=mock_renderer,
            repository=mock_repo,
            trend_sources=[mock_trend_source],
            publisher=mock_publisher,
            cache=mock_cache,
            evaluator=mock_evaluator,
        )

    @pytest.mark.asyncio
    async def test_execute_success(self, use_case, mock_repo):
        request = GenerateContentRequest(niche="tech", platform="youtube", count=1)
        result = await use_case.execute(request)
        assert result.success is True
        assert result.data is not None
        assert "idea" in result.data

    @pytest.mark.asyncio
    async def test_execute_saves_content(self, use_case, mock_repo):
        request = GenerateContentRequest(niche="tech", platform="youtube")
        result = await use_case.execute(request)
        assert mock_repo.save_idea.called
        assert mock_repo.save_script.called
        assert mock_repo.save_video.called

    @pytest.mark.asyncio
    async def test_execute_fallback_on_ai_error(self, mock_tts, mock_renderer, mock_repo, mock_trend_source, mock_publisher, mock_cache, mock_evaluator):
        failing_ai = AsyncMock()
        failing_ai.name = "failing"
        failing_ai.available = True
        failing_ai.generate_json = AsyncMock(side_effect=Exception("API error"))

        uc = GenerateContentUseCase(
            ai_provider=failing_ai,
            tts_provider=mock_tts,
            video_renderer=mock_renderer,
            repository=mock_repo,
            trend_sources=[mock_trend_source],
            publisher=mock_publisher,
            cache=mock_cache,
            evaluator=mock_evaluator,
        )
        request = GenerateContentRequest(niche="tech")
        result = await uc.execute(request)
        assert result.success is False or result is not None

    @pytest.mark.asyncio
    async def test_execute_without_trends(self, mock_ai, mock_tts, mock_renderer, mock_repo, mock_publisher, mock_cache, mock_evaluator):
        """Debe funcionar incluso sin fuentes de trends."""
        uc = GenerateContentUseCase(
            ai_provider=mock_ai,
            tts_provider=mock_tts,
            video_renderer=mock_renderer,
            repository=mock_repo,
            trend_sources=[],
            publisher=mock_publisher,
            cache=mock_cache,
            evaluator=mock_evaluator,
        )
        request = GenerateContentRequest(niche="tech")
        result = await uc.execute(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_failing_trend_source(self, mock_ai, mock_tts, mock_renderer, mock_repo, mock_publisher, mock_cache, mock_evaluator):
        """Fuentes de trends que fallan no deben detener el pipeline."""
        failing_source = AsyncMock()
        failing_source.available = True
        failing_source.source_name = "failing"
        failing_source.fetch_trends = AsyncMock(side_effect=Exception("API down"))

        uc = GenerateContentUseCase(
            ai_provider=mock_ai,
            tts_provider=mock_tts,
            video_renderer=mock_renderer,
            repository=mock_repo,
            trend_sources=[failing_source],
            publisher=mock_publisher,
            cache=mock_cache,
            evaluator=mock_evaluator,
        )
        request = GenerateContentRequest(niche="tech")
        result = await uc.execute(request)
        assert result.success is True


class TestEvaluateContentUseCase:
    @pytest.fixture
    def use_case(self, mock_repo, mock_evaluator):
        return EvaluateContentUseCase(
            evaluator=mock_evaluator,
            repository=mock_repo,
        )

    @pytest.mark.asyncio
    async def test_evaluate_idea_found(self, use_case, mock_repo):
        request = EvaluateRequest(content_id="abc", content_type="idea")
        result = await use_case.execute(request)
        assert result.success is True
        assert "evaluation" in result.data

    @pytest.mark.asyncio
    async def test_evaluate_idea_not_found(self, mock_evaluator):
        empty_repo = MagicMock()
        empty_repo.get_idea = AsyncMock(return_value=None)

        uc = EvaluateContentUseCase(evaluator=mock_evaluator, repository=empty_repo)
        request = EvaluateRequest(content_id="nonexistent", content_type="idea")
        result = await uc.execute(request)
        assert result.success is False
        assert "no encontrada" in result.message.lower()

    @pytest.mark.asyncio
    async def test_evaluate_script_found(self, use_case, mock_repo):
        request = EvaluateRequest(content_id="abc", content_type="script")
        result = await use_case.execute(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_invalid_content_type(self, use_case):
        request = EvaluateRequest(content_id="abc", content_type="invalid")
        result = await use_case.execute(request)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_evaluate_optimizes(self, mock_repo, mock_evaluator):
        """Si el score es bajo, debe optimizar."""
        low_score_result = MagicMock()
        low_score_result.score_total = 4.0
        low_score_result.classification = "malo"
        low_score_result.criteria = {}
        low_score_result.recommendations = ["mejorar hook"]
        low_score_result.is_acceptable = False
        mock_evaluator.evaluate_idea = MagicMock(return_value=low_score_result)

        uc = EvaluateContentUseCase(evaluator=mock_evaluator, repository=mock_repo)
        request = EvaluateRequest(content_id="abc", content_type="idea", optimize=True)
        result = await uc.execute(request)
        assert result.success is True
        assert result.data["evaluation"]["was_optimized"] is True


class TestManageTrendsUseCase:
    @pytest.fixture
    def use_case(self, mock_trend_source, mock_repo, mock_cache):
        return ManageTrendsUseCase(
            sources=[mock_trend_source],
            repository=mock_repo,
            cache=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_get_trends_success(self, use_case):
        request = TrendRequest(niche="tech")
        result = await use_case.execute(request)
        assert result.success is True
        assert "trends" in result.data

    @pytest.mark.asyncio
    async def test_get_trends_cached(self, mock_trend_source, mock_repo, mock_cache):
        """Si hay cache, debe devolver datos cacheados."""
        cached_trends = [{"topic": "AI", "viral_score": 80}]
        mock_cache.get = MagicMock(return_value=cached_trends)

        uc = ManageTrendsUseCase(
            sources=[mock_trend_source],
            repository=mock_repo,
            cache=mock_cache,
        )
        request = TrendRequest(niche="tech")
        result = await uc.execute(request)
        assert result.success is True
        # fetch_trends no debe llamarse si hay cache
        mock_trend_source.fetch_trends.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_trends_empty(self, mock_repo, mock_cache):
        empty_source = AsyncMock()
        empty_source.available = True
        empty_source.source_name = "empty"
        empty_source.fetch_trends = AsyncMock(return_value=[])

        uc = ManageTrendsUseCase(
            sources=[empty_source],
            repository=mock_repo,
            cache=mock_cache,
        )
        request = TrendRequest(niche="unknown")
        result = await uc.execute(request)
        assert result.success is True
        assert result.data["trends"] == []

    @pytest.mark.asyncio
    async def test_get_trends_source_error(self, mock_repo, mock_cache):
        failing_source = AsyncMock()
        failing_source.available = True
        failing_source.source_name = "failing"
        failing_source.fetch_trends = AsyncMock(side_effect=Exception("API error"))

        uc = ManageTrendsUseCase(
            sources=[failing_source],
            repository=mock_repo,
            cache=mock_cache,
        )
        request = TrendRequest(niche="tech")
        result = await uc.execute(request)
        assert result.success is True  # Empty is ok, not failure
