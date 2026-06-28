"""
Research Test Fixtures
=======================
Fixtures compartidos para todos los tests del módulo Research.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_source import ResearchSource, SourceType
from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.services.duplicate_detector import (
    CompositeDuplicateDetector,
    UrlNormalizerStrategy,
    TitleNormalizerStrategy,
)
from research.domain.services.research_scorer import ResearchScorer


# ── Sample topics ────────────────────────────────────


@pytest.fixture
def sample_topic() -> ResearchTopic:
    """Topic de ejemplo para tests."""
    return ResearchTopic(
        title="Nuevo modelo de IA supera a GPT-4",
        description="Un nuevo modelo de IA alcanza resultados sorprendentes",
        content="Contenido extenso sobre el nuevo modelo de IA que supera a GPT-4 en múltiples benchmarks. " * 10,
        source=ResearchSource.google_news(),
        url="https://example.com/ai/nuevo-modelo",
        author="Test Author",
        published_at=datetime.now(timezone.utc) - timedelta(hours=3),
    )


@pytest.fixture
def approved_topic() -> ResearchTopic:
    """Topic ya aprobado para tests de estados terminales."""
    topic = ResearchTopic(
        title="Topic aprobado",
        description="Test desc",
        content="Contenido de prueba. " * 5,
        source=ResearchSource.google_news(),
        url="https://example.com/approved",
        author="Test Author",
    )
    topic.status = ResearchStatus.APPROVED
    topic.reviewed_at = datetime.now(timezone.utc)
    return topic


@pytest.fixture
def rejected_topic() -> ResearchTopic:
    """Topic ya rechazado para tests de estados terminales."""
    topic = ResearchTopic(
        title="Topic rechazado",
        description="Test desc",
        content="Contenido de prueba. " * 5,
        source=ResearchSource.google_news(),
        url="https://example.com/rejected",
        author="Test Author",
    )
    topic.status = ResearchStatus.REJECTED
    topic.reviewed_at = datetime.now(timezone.utc)
    return topic


@pytest.fixture
def rejected_topic(sample_topic: ResearchTopic) -> ResearchTopic:
    """Topic ya rechazado para tests de estados terminales."""
    topic = sample_topic
    topic.status = ResearchStatus.REJECTED
    topic.reviewed_at = datetime.now(timezone.utc)
    return topic


@pytest.fixture
def topics_batch() -> list[ResearchTopic]:
    """Batch de topics para tests de descubrimiento automático."""
    return [
        ResearchTopic(
            title=f"Noticia de prueba #{i}",
            description=f"Descripción de la noticia #{i}",
            content=f"Contenido de la noticia de prueba número {i}. " * 5,
            source=ResearchSource(name="mock", type=SourceType.AUTOMATIC, reliability=70),
            url=f"https://example.com/news/{i}",
        )
        for i in range(5)
    ]


# ── Domain Services ──────────────────────────────────


@pytest.fixture
def duplicate_detector() -> CompositeDuplicateDetector:
    """Detector de duplicados con estrategias URL y título."""
    return CompositeDuplicateDetector([
        UrlNormalizerStrategy(),
        TitleNormalizerStrategy(),
    ])


@pytest.fixture
def scorer() -> ResearchScorer:
    """Scorer básico (sin IA)."""
    return ResearchScorer()


# ── In-memory Repository ─────────────────────────────


class InMemoryResearchRepository:
    """
    Repositorio en memoria para tests.
    Implementa ResearchRepository (Protocol).
    """

    def __init__(self):
        self._topics: dict[str, ResearchTopic] = {}

    async def save(self, topic: ResearchTopic) -> None:
        self._topics[str(topic.id)] = topic

    async def save_many(self, topics: list[ResearchTopic]) -> None:
        for topic in topics:
            self._topics[str(topic.id)] = topic

    async def find_by_id(self, topic_id) -> ResearchTopic | None:
        return self._topics.get(str(topic_id))

    async def find_by_status(self, status, limit=50) -> list[ResearchTopic]:
        result = [t for t in self._topics.values() if t.status == status]
        result.sort(key=lambda t: t.score.total, reverse=True)
        return result[:limit]

    async def find_by_duplicate_hash(self, hash_val) -> list[ResearchTopic]:
        return [
            t for t in self._topics.values()
            if t.duplicate_hash == hash_val
        ]

    async def find_pending_review(self, limit=20) -> list[ResearchTopic]:
        return await self.find_by_status(ResearchStatus.PENDING_REVIEW, limit)

    async def find_all(self, limit=50, offset=0) -> list[ResearchTopic]:
        sorted_topics = sorted(
            self._topics.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        return sorted_topics[offset:offset + limit]

    async def count_by_status(self, status) -> int:
        return sum(1 for t in self._topics.values() if t.status == status)

    async def delete(self, topic_id) -> None:
        self._topics.pop(str(topic_id), None)


@pytest.fixture
def in_memory_repo() -> InMemoryResearchRepository:
    """Repositorio en memoria para tests."""
    return InMemoryResearchRepository()
