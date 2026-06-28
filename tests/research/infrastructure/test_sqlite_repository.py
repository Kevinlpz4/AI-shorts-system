"""
Tests para SQLiteResearchRepository.
"""
import pytest
from uuid import uuid4

from research.infrastructure.persistence.sqlite_repository import SQLiteResearchRepository
from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.value_objects.research_source import ResearchSource
from research.domain.value_objects.research_score import ResearchScore


@pytest.fixture
def sqlite_repo(tmp_path):
    """Repositorio SQLite en archivo temporal."""
    db_path = str(tmp_path / "test_research.db")
    return SQLiteResearchRepository(db_path=db_path)


class TestSQLiteResearchRepository:

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, sqlite_repo):
        """Guardar y recuperar un topic por ID."""
        topic = ResearchTopic(
            title="Test SQLite",
            description="Test desc",
            content="Test content",
            source=ResearchSource.manual(),
        )
        await sqlite_repo.save(topic)

        retrieved = await sqlite_repo.find_by_id(topic.id)
        assert retrieved is not None
        assert retrieved.id == topic.id
        assert retrieved.title == "Test SQLite"
        assert retrieved.status == ResearchStatus.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, sqlite_repo):
        """Buscar un ID que no existe debe retornar None."""
        result = await sqlite_repo.find_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_update(self, sqlite_repo):
        """Guardar el mismo topic dos veces debe actualizarlo (upsert)."""
        topic = ResearchTopic(title="Original")
        await sqlite_repo.save(topic)

        topic.title = "Actualizado"
        topic.description = "Nueva desc"
        await sqlite_repo.save(topic)

        retrieved = await sqlite_repo.find_by_id(topic.id)
        assert retrieved.title == "Actualizado"
        assert retrieved.description == "Nueva desc"

    @pytest.mark.asyncio
    async def test_save_many(self, sqlite_repo, topics_batch):
        """Guardar múltiples topics."""
        await sqlite_repo.save_many(topics_batch)

        all_topics = await sqlite_repo.find_all(limit=50)
        assert len(all_topics) == 5

    @pytest.mark.asyncio
    async def test_find_by_status(self, sqlite_repo, sample_topic, approved_topic):
        """Filtrar topics por estado."""
        await sqlite_repo.save(sample_topic)
        await sqlite_repo.save(approved_topic)

        pending = await sqlite_repo.find_by_status(ResearchStatus.PENDING_REVIEW)
        approved_list = await sqlite_repo.find_by_status(ResearchStatus.APPROVED)

        assert len(pending) >= 1
        assert len(approved_list) >= 1
        assert all(t.status == ResearchStatus.PENDING_REVIEW for t in pending)
        assert all(t.status == ResearchStatus.APPROVED for t in approved_list)

    @pytest.mark.asyncio
    async def test_find_by_duplicate_hash(self, sqlite_repo):
        """Buscar topics por hash de duplicado."""
        t1 = ResearchTopic(title="A", duplicate_hash="abc123")
        t2 = ResearchTopic(title="B (dup)", duplicate_hash="abc123")
        t3 = ResearchTopic(title="C", duplicate_hash="xyz789")

        await sqlite_repo.save(t1)
        await sqlite_repo.save(t2)
        await sqlite_repo.save(t3)

        results = await sqlite_repo.find_by_duplicate_hash("abc123")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_find_pending_review(self, sqlite_repo, sample_topic, approved_topic):
        """Listar topics pendientes de revisión."""
        await sqlite_repo.save(sample_topic)
        await sqlite_repo.save(approved_topic)

        pending = await sqlite_repo.find_pending_review()
        assert len(pending) >= 1
        assert all(t.status == ResearchStatus.PENDING_REVIEW for t in pending)

    @pytest.mark.asyncio
    async def test_find_all_with_pagination(self, sqlite_repo, topics_batch):
        """Listar topics con paginación."""
        await sqlite_repo.save_many(topics_batch)

        page1 = await sqlite_repo.find_all(limit=2, offset=0)
        page2 = await sqlite_repo.find_all(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        # IDs deben ser diferentes entre páginas
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_count_by_status(self, sqlite_repo):
        """Contar topics por estado."""
        t1 = ResearchTopic(title="Pending")
        t2 = ResearchTopic(title="Approved")
        t2.approve()

        await sqlite_repo.save(t1)
        await sqlite_repo.save(t2)

        assert await sqlite_repo.count_by_status(ResearchStatus.PENDING_REVIEW) >= 1
        assert await sqlite_repo.count_by_status(ResearchStatus.APPROVED) >= 1
        assert await sqlite_repo.count_by_status(ResearchStatus.REJECTED) == 0

    @pytest.mark.asyncio
    async def test_delete(self, sqlite_repo):
        """Eliminar un topic."""
        topic = ResearchTopic(title="To delete")
        await sqlite_repo.save(topic)

        assert await sqlite_repo.find_by_id(topic.id) is not None

        await sqlite_repo.delete(topic.id)
        assert await sqlite_repo.find_by_id(topic.id) is None

    @pytest.mark.asyncio
    async def test_save_preserves_score(self, sqlite_repo):
        """Guardar y recuperar debe preservar el score."""
        topic = ResearchTopic(title="Score test")
        topic.score = ResearchScore(relevance=80, popularity=70, recency=60, source_reliability=90)
        await sqlite_repo.save(topic)

        retrieved = await sqlite_repo.find_by_id(topic.id)
        assert retrieved.score.relevance == 80
        assert retrieved.score.popularity == 70
        assert retrieved.score.recency == 60
        assert retrieved.score.source_reliability == 90
        assert retrieved.score.total == topic.score.total

    @pytest.mark.asyncio
    async def test_save_preserves_source(self, sqlite_repo):
        """Guardar y recuperar debe preservar la fuente."""
        topic = ResearchTopic(
            title="Source test",
            source=ResearchSource.google_news(),
        )
        await sqlite_repo.save(topic)

        retrieved = await sqlite_repo.find_by_id(topic.id)
        assert retrieved.source.name == "google-news"
        assert retrieved.source.reliability == 80

    @pytest.mark.asyncio
    async def test_save_truncates_long_content(self, sqlite_repo):
        """Contenido muy largo debe truncarse."""
        long_content = "X" * 600_000  # 600KB
        topic = ResearchTopic(
            title="Long content test",
            content=long_content,
        )
        await sqlite_repo.save(topic)

        retrieved = await sqlite_repo.find_by_id(topic.id)
        assert len(retrieved.content) <= 500_000  # Truncado al límite
