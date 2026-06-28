"""
Tests para la entidad ResearchTopic (Aggregate Root).
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime, timezone

from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_source import ResearchSource
from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.exceptions import ResearchAlreadyReviewedError
from research.domain.events import TopicDiscovered, TopicApproved, TopicRejected


class TestResearchTopicCreation:

    def test_create_minimal(self):
        """Se puede crear un topic solo con título."""
        topic = ResearchTopic(title="Test")
        assert topic.title == "Test"
        assert isinstance(topic.id, UUID)
        assert topic.status == ResearchStatus.PENDING_REVIEW
        assert topic.score == ResearchScore()
        assert topic.source == ResearchSource.manual()
        assert topic.created_at is not None
        assert topic._events == []

    def test_create_with_all_fields(self, sample_topic):
        topic = sample_topic
        assert topic.title == "Nuevo modelo de IA supera a GPT-4"
        assert topic.url == "https://example.com/ai/nuevo-modelo"
        assert topic.author == "Test Author"
        assert topic.published_at is not None

    def test_default_status_is_pending_review(self):
        """Regla de negocio: los topics nuevos siempre van a PENDING_REVIEW."""
        topic = ResearchTopic(title="Test")
        assert topic.status == ResearchStatus.PENDING_REVIEW
        assert topic.status.is_reviewable is True


class TestResearchTopicApprove:

    def test_approve_pending_topic(self, sample_topic):
        """Aprobar un topic en PENDING_REVIEW debe funcionar."""
        assert sample_topic.status == ResearchStatus.PENDING_REVIEW
        assert sample_topic.reviewed_at is None

        sample_topic.approve()

        assert sample_topic.status == ResearchStatus.APPROVED
        assert sample_topic.reviewed_at is not None

    def test_approve_generates_event(self, sample_topic):
        """Approve debe generar un TopicApproved event."""
        sample_topic.approve()
        events = sample_topic.pull_events()

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, TopicApproved)
        assert event.topic_id == sample_topic.id
        assert event.title == sample_topic.title

    def test_approve_clears_events(self, sample_topic):
        """pull_events debe limpiar la lista de eventos."""
        sample_topic.approve()
        events = sample_topic.pull_events()
        assert len(events) == 1

        # Segunda llamada debe retornar vacío
        assert sample_topic.pull_events() == []

    def test_approve_approved_topic_raises(self, approved_topic):
        """No se puede aprobar un topic ya aprobado."""
        with pytest.raises(ResearchAlreadyReviewedError):
            approved_topic.approve()

    def test_approve_rejected_topic_raises(self, rejected_topic):
        """No se puede aprobar un topic ya rechazado."""
        with pytest.raises(ResearchAlreadyReviewedError):
            rejected_topic.approve()


class TestResearchTopicReject:

    def test_reject_pending_topic(self, sample_topic):
        """Rechazar un topic en PENDING_REVIEW debe funcionar."""
        sample_topic.reject(reason="No es relevante")
        assert sample_topic.status == ResearchStatus.REJECTED
        assert sample_topic.reviewed_at is not None

    def test_reject_generates_event(self, sample_topic):
        """Reject debe generar un TopicRejected event."""
        sample_topic.reject(reason="No relevante")
        events = sample_topic.pull_events()

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, TopicRejected)
        assert event.topic_id == sample_topic.id
        assert event.reason == "No relevante"

    def test_reject_empty_reason(self, sample_topic):
        """Se puede rechazar sin razón."""
        sample_topic.reject()
        assert sample_topic.status == ResearchStatus.REJECTED

    def test_reject_approved_topic_raises(self, approved_topic):
        """No se puede rechazar un topic ya aprobado."""
        with pytest.raises(ResearchAlreadyReviewedError):
            approved_topic.reject()

    def test_reject_rejected_topic_raises(self, rejected_topic):
        """No se puede rechazar un topic ya rechazado."""
        with pytest.raises(ResearchAlreadyReviewedError):
            rejected_topic.reject()


class TestResearchTopicMarkAsDiscovered:

    def test_mark_as_discovered_generates_event(self, sample_topic):
        """mark_as_discovered debe generar TopicDiscovered."""
        sample_topic.mark_as_discovered()
        events = sample_topic.pull_events()

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, TopicDiscovered)
        assert event.topic_id == sample_topic.id
        assert event.source_name == sample_topic.source.name

    def test_mark_twice_generates_two_events(self, sample_topic):
        """Llamar mark_as_discovered dos veces acumula dos eventos."""
        sample_topic.mark_as_discovered()
        sample_topic.mark_as_discovered()
        events = sample_topic.pull_events()
        assert len(events) == 2


class TestResearchTopicLifecycle:

    def test_full_lifecycle(self, sample_topic):
        """Ciclo de vida completo: discovered → approved."""
        # 1. Discovered
        sample_topic.mark_as_discovered()
        assert sample_topic.status == ResearchStatus.PENDING_REVIEW

        # 2. Approve
        sample_topic.approve()
        assert sample_topic.status == ResearchStatus.APPROVED

        # 3. Events acumulados
        events = sample_topic.pull_events()
        assert len(events) == 2
        assert isinstance(events[0], TopicDiscovered)
        assert isinstance(events[1], TopicApproved)

    def test_reject_after_discover(self, sample_topic):
        """Ciclo: discovered → rejected."""
        sample_topic.mark_as_discovered()
        sample_topic.reject(reason="Duplicado")
        assert sample_topic.status == ResearchStatus.REJECTED

    def test_cannot_review_after_approve(self, sample_topic):
        """No se puede hacer nada después de aprobado."""
        sample_topic.approve()
        with pytest.raises(ResearchAlreadyReviewedError):
            sample_topic.reject()
        with pytest.raises(ResearchAlreadyReviewedError):
            sample_topic.approve()


class TestResearchTopicStr:

    def test_str_representation(self, sample_topic):
        """__str__ debe mostrar título, estado y score."""
        result = str(sample_topic)
        assert "ResearchTopic" in result
        assert sample_topic.status.value in result
