"""
Tests para Proveedores Mock de Infraestructura.
"""
import pytest
from infrastructure.ai.mock_provider import MockAIProvider
from infrastructure.cache.memory_cache import MemoryCache
from infrastructure.trends.mock_source import MockTrendSource
from infrastructure.tts.mock_provider import MockTTSProvider
from infrastructure.publishing.mock_publisher import MockPublisher
from infrastructure.video.mock_renderer import MockVideoRenderer
from domain.entities.trend import Trend, TrendSource
from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.video import VideoAsset
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration


class TestMockAIProvider:
    @pytest.fixture
    def provider(self):
        return MockAIProvider()

    def test_name(self, provider):
        assert provider.name == "mock"

    def test_available(self, provider):
        assert provider.available is True

    @pytest.mark.asyncio
    async def test_generate_returns_string(self, provider):
        result = await provider.generate("generá una idea")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_json_returns_dict(self, provider):
        result = await provider.generate_json("generá una idea")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_generate_ideas_needs_trends(self, provider):
        trends = [
            Trend(id="t1", topic="AI", source=TrendSource("news", "web"), viral_score=ViralScore(80)),
            Trend(id="t2", topic="Blockchain", source=TrendSource("news", "web"), viral_score=ViralScore(70)),
        ]
        ideas = await provider.generate_ideas(trends=trends, niche="tech", count=3)
        assert len(ideas) == 3
        for idea in ideas:
            assert isinstance(idea, ContentIdea)
            assert idea.hook
            assert 0 <= idea.viral_score.value <= 100

    @pytest.mark.asyncio
    async def test_generate_ideas_with_empty_trends(self, provider):
        ideas = await provider.generate_ideas(trends=[], niche="tech", count=2)
        assert len(ideas) == 2

    @pytest.mark.asyncio
    async def test_generate_script(self, provider):
        idea = ContentIdea(hook="Hook", topic="AI", viral_score=ViralScore(70))
        script = await provider.generate_script(idea=idea, duration=45, tone="humor")
        assert isinstance(script, Script)
        assert script.idea_id == idea.id
        assert script.topic == "AI"

    @pytest.mark.asyncio
    async def test_generate_json_on_script_prompt(self, provider):
        """generate_json con prompt de guion debe parsear JSON."""
        result = await provider.generate_json("generá un guion para video")
        assert isinstance(result, dict)


class TestMemoryCache:
    @pytest.fixture
    def cache(self):
        return MemoryCache(default_ttl=60)

    def test_set_and_get(self, cache):
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing(self, cache):
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = MemoryCache(default_ttl=0)
        cache.set("key", "value")
        import time
        time.sleep(0.1)
        assert cache.get("key") is None

    def test_clear(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_stats(self, cache):
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("missing")  # miss
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_hit_rate(self, cache):
        cache.set("a", 1)
        cache.get("a")
        cache.get("a")
        cache.get("x")
        stats = cache.get_stats()
        assert stats["hit_rate"] == pytest.approx(2/3, rel=1e-3)

    def test_make_key(self):
        key = MemoryCache.make_key("test", 123)
        assert isinstance(key, str)
        assert len(key) == 32  # md5 hexdigest

    def test_custom_ttl(self, cache):
        cache.set("key", "val", ttl=999)
        assert cache.get("key") == "val"


class TestMockTrendSource:
    @pytest.fixture
    def source(self):
        return MockTrendSource(source_type="news")

    def test_source_name(self, source):
        assert source.source_name == "mock-news"

    def test_available(self, source):
        assert source.available is True

    @pytest.mark.asyncio
    async def test_fetch_trends(self, source):
        trends = await source.fetch_trends(niche="tecnología", limit=5)
        assert len(trends) <= 5
        assert len(trends) > 0
        for t in trends:
            assert isinstance(t, Trend)
            assert t.topic
            assert 0 <= int(t.viral_score) <= 100

    @pytest.mark.asyncio
    async def test_fetch_trends_unknown_niche(self, source):
        trends = await source.fetch_trends(niche="unknown", limit=3)
        assert len(trends) > 0  # Should use defaults

    @pytest.mark.asyncio
    async def test_fetch_trends_limit_zero(self, source):
        trends = await source.fetch_trends(niche="tech", limit=0)
        assert len(trends) == 0


class TestMockTTSProvider:
    @pytest.fixture
    def tts(self, tmp_path):
        return MockTTSProvider(output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_synthesize(self, tts):
        audio = await tts.synthesize(text="Hola mundo, esto es una prueba")
        assert audio.status == "mock"
        assert audio.duration > 0
        assert audio.audio_path != ""

    @pytest.mark.asyncio
    async def test_synthesize_with_custom_path(self, tts, tmp_path):
        path = str(tmp_path / "custom.mp3")
        audio = await tts.synthesize(text="Test", output_path=path)
        assert path in audio.audio_path

    def test_name(self, tts):
        assert tts.name == "mock-tts"

    def test_available(self, tts):
        assert tts.available is True

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, tts):
        audio = await tts.synthesize(text="")
        assert audio.status == "mock"


class TestMockPublisher:
    @pytest.fixture
    def publisher(self):
        return MockPublisher(platform_name="youtube")

    def test_platform(self, publisher):
        assert publisher.platform == "youtube"

    @pytest.mark.asyncio
    async def test_publish(self, publisher):
        video = VideoAsset(id="v1", video_path="/tmp/v.mp4", duration=45)
        result = await publisher.publish(video=video, title="Test")
        assert result.is_success is True
        assert result.platform == "youtube"
        assert "youtube.com" in result.url

    @pytest.mark.asyncio
    async def test_publish_with_all_fields(self, publisher):
        video = VideoAsset(id="v1", video_path="/tmp/v.mp4", duration=45)
        result = await publisher.publish(
            video=video,
            title="Título",
            description="Descripción",
            tags=["tag1"],
        )
        assert result.is_success is True


class TestMockVideoRenderer:
    @pytest.fixture
    def renderer(self, tmp_path):
        return MockVideoRenderer(output_dir=str(tmp_path))

    def test_available(self, renderer):
        assert renderer.available is True

    @pytest.mark.asyncio
    async def test_render(self, renderer):
        script = Script(hook="Hook", body="Body", cta="CTA", duration=Duration(45))
        video = await renderer.render(audio_path="/tmp/audio.mp3", script=script)
        assert isinstance(video, VideoAsset)
        assert video.status == "rendered"
        assert video.duration == 45.0
        assert video.width == 1080

    @pytest.mark.asyncio
    async def test_render_custom_aspect(self, renderer):
        script = Script(duration=Duration(30))
        video = await renderer.render(audio_path="/tmp/a.mp3", script=script, aspect_ratio="1:1")
        assert video.status == "rendered"
