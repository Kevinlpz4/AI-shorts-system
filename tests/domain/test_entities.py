"""
Tests para Entities del dominio.
"""
import pytest
from datetime import datetime

from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration
from domain.value_objects.hook_type import HookType
from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.hook import Hook
from domain.entities.trend import Trend, TrendSource
from domain.entities.voice_audio import VoiceAudio
from domain.entities.video import VideoAsset


class TestContentIdea:
    """Tests para ContentIdea — aggregate root de generación."""

    def test_create_with_minimal_fields(self):
        idea = ContentIdea(hook="Hook", topic="Topic")
        assert idea.hook == "Hook"
        assert idea.topic == "Topic"
        assert idea.viral_score.value == 50
        assert idea.format == "story"
        assert idea.target_audience == "general"

    def test_create_with_all_fields(self):
        idea = ContentIdea(
            hook="Hook",
            topic="Topic",
            description="Desc",
            target_audience="devs",
            format="list",
            viral_score=ViralScore(80),
            keywords=["tech"],
            trend_id="trend_1",
        )
        assert idea.viral_score.value == 80
        assert idea.format == "list"

    def test_is_viable(self):
        good = ContentIdea(hook="12345", topic="T", viral_score=ViralScore(60))
        assert good.is_viable() is True

        no_hook = ContentIdea(hook="ab", topic="T", viral_score=ViralScore(80))
        assert no_hook.is_viable() is False

        low_score = ContentIdea(hook="12345", topic="T", viral_score=ViralScore(50))
        assert low_score.is_viable() is False  # 50 no es promising (< 60)

        bad = ContentIdea(hook="ab", topic="T", viral_score=ViralScore(20))
        assert bad.is_viable() is False

    def test_evaluate_hook_quality(self):
        idea = ContentIdea(hook="¿El secreto que nadie te cuenta? 5 cosas", topic="T")
        score = idea.evaluate_hook_quality()
        assert 0 <= score <= 100
        assert score > 50  # good hook should score above baseline

    def test_evaluate_hook_quality_baseline(self):
        idea = ContentIdea(hook="Hola", topic="T")
        score = idea.evaluate_hook_quality()
        assert score >= 50  # baseline 50 + "Hola" is <= 15 words (+15)

    def test_to_dict(self):
        idea = ContentIdea(hook="Hook", topic="Topic", viral_score=ViralScore(75))
        d = idea.to_dict()
        assert d["hook"] == "Hook"
        assert d["viral_score"] == 75
        assert d["format"] == "story"

    def test_auto_id_on_create(self):
        idea1 = ContentIdea(hook="A", topic="B")
        idea2 = ContentIdea(hook="A", topic="B")
        assert idea1.id != idea2.id

    def test_mutable_fields(self):
        idea = ContentIdea(hook="Old", topic="Old")
        idea.hook = "New hook"
        idea.topic = "New topic"
        assert idea.hook == "New hook"
        assert idea.topic == "New topic"


class TestScript:
    """Tests para Script — guion para short."""

    def test_create_with_minimal_fields(self):
        script = Script()
        assert script.id is not None
        assert script.duration.seconds == 45

    def test_create_with_fields(self):
        script = Script(
            idea_id="idea_1",
            topic="AI",
            hook="¿Sabías esto?",
            body="Contenido del video aquí. Esto es importante.",
            cta="Seguime para más",
            duration=Duration(60),
            tone="humor",
            format="list",
        )
        assert script.topic == "AI"
        assert script.word_count > 0

    def test_full_text_property(self):
        script = Script(hook="Hook", body="Body content", cta="CTA")
        assert script.full_text == "Hook. Body content CTA"

    def test_word_count(self):
        script = Script(hook="Hola", body="Mundo cruel", cta="Adiós")
        assert script.word_count == 4

    def test_is_valid_good_script(self):
        script = Script(
            hook="Un hook largo que cumple el mínimo",
            body="x" * 50,
            cta="seguime",
        )
        assert script.is_valid() is True

    def test_is_valid_short_hook(self):
        script = Script(hook="corto", body="x" * 50, cta="seguime")
        assert script.is_valid() is False

    def test_estimate_retention_baseline(self):
        script = Script()
        score = script.estimate_retention()
        assert 0 <= score <= 100

    def test_estimate_retention_optimal(self):
        script = Script(
            hook="A" * 15,
            body="Oración. Otra. Más. " * 5,
            cta="Seguime ahora",
            duration=Duration(45),
        )
        score = script.estimate_retention()
        assert score > 50

    def test_to_dict(self):
        script = Script(hook="Hook", body="Body", cta="CTA", tone="humor")
        d = script.to_dict()
        assert d["hook"] == "Hook"
        assert d["tone"] == "humor"


class TestHook:
    """Tests para Hook — un hook viral."""

    def test_create_defaults(self):
        hook = Hook()
        assert hook.hook_type == HookType.STATEMENT
        assert hook.score == 50
        assert hook.text == ""

    def test_create_with_text(self):
        hook = Hook(text="¿Sabías esto?", hook_type=HookType.QUESTION)
        assert hook.text == "¿Sabías esto?"
        assert hook.hook_type == HookType.QUESTION

    def test_is_strong(self):
        assert Hook(text="x", score=80).is_strong is True
        assert Hook(text="x", score=50).is_strong is False

    def test_length_quality(self):
        assert Hook(text="uno dos tres", score=50).length_quality == "excelente"
        assert Hook(text=" ".join(["word"] * 10), score=50).length_quality == "bueno"
        assert Hook(text=" ".join(["word"] * 14), score=50).length_quality == "aceptable"
        assert Hook(text=" ".join(["word"] * 20), score=50).length_quality == "largo"

    def test_to_dict(self):
        hook = Hook(text="Test", hook_type=HookType.REVEAL, score=85)
        d = hook.to_dict()
        assert d["text"] == "Test"
        assert d["type"] == "reveal"
        assert d["score"] == 85

    def test_hook_type_from_string(self):
        hook = Hook(text="Test", hook_type="question")
        assert hook.hook_type == HookType.QUESTION


class TestTrend:
    """Tests para Trend — una tendencia."""

    def test_create_trend(self):
        source = TrendSource(name="news", type="twitter")
        trend = Trend(
            id="t1",
            topic="AI Revolution",
            source=source,
            viral_score=ViralScore(85),
        )
        assert trend.topic == "AI Revolution"
        assert trend.viral_score.value == 85
        assert trend.engagement == 0

    def test_is_relevant_for_niche(self):
        source = TrendSource(name="news", type="twitter")
        trend = Trend(
            id="t1",
            topic="AI in Healthcare",
            source=source,
            viral_score=ViralScore(80),
            category="tecnología",
            keywords=["ai", "health"],
        )
        assert trend.is_relevant_for("tecnología") is True
        assert trend.is_relevant_for("salud") is False  # not in topic/category/keywords
        assert trend.is_relevant_for("ai") is True  # in keywords

    def test_is_relevant_empty_keywords(self):
        source = TrendSource(name="news", type="twitter")
        trend = Trend(id="t1", topic="Tech", source=source, viral_score=ViralScore(50))
        assert trend.is_relevant_for("tech") is True  # in topic
        assert trend.is_relevant_for("nada") is False

    def test_to_dict(self):
        source = TrendSource(name="news", type="twitter")
        trend = Trend(
            id="t1",
            topic="AI",
            source=source,
            viral_score=ViralScore(80),
            engagement=5000,
        )
        d = trend.to_dict()
        assert d["id"] == "t1"
        assert d["viral_score"] == 80
        assert d["engagement"] == 5000
        assert d["source"] == "news"

    def test_trend_source_dataclass(self):
        ts = TrendSource(name="test", type="news")
        assert ts.name == "test"
        assert ts.type == "news"


class TestVoiceAudio:
    """Tests para VoiceAudio — audio generado por TTS."""

    def test_create_defaults(self):
        audio = VoiceAudio()
        assert audio.status == "pending"
        assert audio.duration == 0.0

    def test_is_mock(self):
        audio = VoiceAudio(status="mock")
        assert audio.is_mock is True
        assert audio.is_success is False

    def test_is_success(self):
        audio = VoiceAudio(status="success")
        assert audio.is_success is True

    def test_to_dict(self):
        audio = VoiceAudio(
            id="v1",
            text="Hola mundo",
            audio_path="/tmp/audio.mp3",
            duration=30.5,
            voice_id="rachel",
            provider="mock-tts",
            status="mock",
        )
        d = audio.to_dict()
        assert d["duration"] == 30.5
        assert d["status"] == "mock"


class TestVideoAsset:
    """Tests para VideoAsset — video renderizado."""

    def test_create_defaults(self):
        video = VideoAsset()
        assert video.status == "pending"
        assert video.width == 1080
        assert video.height == 1920

    def test_aspect_ratio(self):
        video = VideoAsset()
        assert video.aspect_ratio == "1080:1920"

    def test_is_rendered_success(self):
        video = VideoAsset(status="rendered", file_size=1000)
        assert video.is_rendered is True

    def test_is_rendered_pending(self):
        video = VideoAsset(status="pending")
        assert video.is_rendered is False

    def test_is_rendered_no_file(self):
        video = VideoAsset(status="rendered", file_size=0)
        assert video.is_rendered is False

    def test_to_dict(self):
        video = VideoAsset(
            id="v1",
            video_path="/tmp/video.mp4",
            width=1080,
            height=1920,
            duration=45.0,
            fps=30,
            file_size=5_242_880,
        )
        d = video.to_dict()
        assert d["resolution"] == "1080x1920"
        assert d["file_size_mb"] == 5.0
