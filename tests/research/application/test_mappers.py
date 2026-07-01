"""
Tests para Mappers de la capa de aplicación.
"""
from research.application.mappers import topic_to_dto, event_to_dict
from research.domain.events import TopicDiscovered, TopicApproved
from research.domain.services.research_scorer import ResearchScorer
from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_source import ResearchSource


class TestTopicToDTO:

    def test_topic_to_dto(self):
        """Un topic completo debe mapear correctamente a DTO."""
        topic = ResearchTopic(
            title="Nuevo modelo de IA supera a GPT-4",
            description="Un nuevo modelo de IA alcanza resultados sorprendentes",
            content="Contenido extenso sobre el nuevo modelo de IA. " * 20,
            source=ResearchSource.google_news(),
            url="https://example.com/ai/nuevo-modelo",
            author="Test Author",
        )
        # Calcular score para que no sea 0
        scorer = ResearchScorer()
        topic.score = scorer.calculate(topic)

        dto = topic_to_dto(topic)

        assert dto.id == topic.id
        assert dto.title == topic.title
        assert dto.description == topic.description
        assert dto.source_name == "google-news"
        assert dto.source_type == "automatic"
        assert dto.status == "pending_review"
        assert dto.score_total > 0
        assert dto.url == topic.url
        assert dto.author == "Test Author"
        assert dto.created_at is not None

    def test_content_truncated(self, sample_topic):
        """content_preview debe truncar a 200 chars."""
        dto = topic_to_dto(sample_topic)
        assert len(dto.content_preview) <= 200

    def test_score_components_in_dto(self, sample_topic):
        """DTO debe incluir componentes del score."""
        dto = topic_to_dto(sample_topic)
        assert "relevance" in dto.score_components
        assert "popularity" in dto.score_components
        assert "recency" in dto.score_components
        assert "reliability" in dto.score_components


class TestEventToDict:

    def test_topic_discovered_to_dict(self):
        event = TopicDiscovered(
            topic_id="550e8400-e29b-41d4-a716-446655440000",
            title="Test",
            source_name="mock",
            score_total=75.5,
        )
        result = event_to_dict(event)

        assert result["type"] == "TopicDiscovered"
        assert result["data"]["title"] == "Test"
        assert result["data"]["source_name"] == "mock"
        assert result["data"]["score_total"] == 75.5

    def test_topic_approved_to_dict(self):
        import uuid
        uid = uuid.uuid4()
        event = TopicApproved(
            topic_id=uid,
            title="Noticia aprobada",
        )
        result = event_to_dict(event)

        assert result["type"] == "TopicApproved"
        assert result["data"]["topic_id"] == str(uid)
        assert result["data"]["title"] == "Noticia aprobada"
