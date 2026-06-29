"""
Tests para Script Mappers (application/use_cases/script/mappers.py).
"""
import pytest
from datetime import datetime, timezone, timedelta

from application.use_cases.script.mappers import research_topic_to_content_idea
from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_source import ResearchSource
from research.domain.value_objects.research_score import ResearchScore


class TestResearchTopicToContentIdea:

    def test_basic_conversion(self):
        """Convertir ResearchTopic básico debe dar ContentIdea válida."""
        topic = ResearchTopic(
            title="Nuevo modelo de IA supera a GPT-4",
            description="Un avance sorprendente en IA",
            content="Contenido extenso sobre el nuevo modelo." * 10,
            source=ResearchSource.google_news(),
            url="https://example.com/ai/news",
        )
        idea = research_topic_to_content_idea(topic)

        assert idea.topic == "Nuevo modelo de IA supera a GPT-4"
        assert idea.hook == "Nuevo modelo de IA supera a GPT-4"
        assert idea.description == "Un avance sorprendente en IA"
        assert idea.format == "story"
        assert idea.target_audience == "general"
        assert idea.trend_id == str(topic.id)

    def test_preserves_score(self):
        """El score del ResearchTopic debe pasar a ViralScore."""
        topic = ResearchTopic(
            title="Test score",
            source=ResearchSource.manual(),
        )
        topic.score = ResearchScore(relevance=80, popularity=70, recency=60, source_reliability=90)
        idea = research_topic_to_content_idea(topic)

        assert idea.viral_score.value == topic.score.total

    def test_custom_tone_and_format(self):
        """Los parámetros tone y format deben pasarse correctamente."""
        topic = ResearchTopic(
            title="Test params",
            source=ResearchSource.manual(),
        )
        idea = research_topic_to_content_idea(topic, tone="humor", format="list")

        assert idea.format == "list"

    def test_hook_truncated_to_100_chars(self):
        """El hook debe truncarse a 100 caracteres."""
        long_title = "A" * 200
        topic = ResearchTopic(title=long_title, source=ResearchSource.manual())
        idea = research_topic_to_content_idea(topic)

        assert len(idea.hook) == 100
        assert idea.hook == "A" * 100

    def test_empty_title(self):
        """Title vacío debe dar hook vacío."""
        topic = ResearchTopic(title="", source=ResearchSource.manual())
        idea = research_topic_to_content_idea(topic)

        assert idea.hook == ""
        assert idea.topic == ""

    def test_pure_function(self):
        """La función debe ser pura: mismo input → mismo output."""
        topic = ResearchTopic(title="Test", source=ResearchSource.manual())
        result1 = research_topic_to_content_idea(topic)
        result2 = research_topic_to_content_idea(topic)

        assert result1.hook == result2.hook
        assert result1.topic == result2.topic
