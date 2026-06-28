"""
Tests para Casos de Uso del módulo Research.
"""
import pytest
from uuid import uuid4

from research.application.dtos import (
    ManualInputDTO,
    AutoDiscoverDTO,
    ReviewDecisionDTO,
    ListTopicsQuery,
)
from research.application.use_cases.manual_input import RegisterManualInputUseCase
from research.application.use_cases.auto_discover import AutoDiscoverTopicsUseCase
from research.application.use_cases.approve_topic import ApproveTopicUseCase
from research.application.use_cases.reject_topic import RejectTopicUseCase
from research.application.use_cases.list_topics import ListTopicsUseCase
from research.domain.exceptions import (
    ResearchTopicNotFoundError,
    ResearchAlreadyReviewedError,
    InvalidManualInputError,
)
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.entities.research_topic import ResearchTopic


# ── RegisterManualInputUseCase ───────────────────────


class TestRegisterManualInputUseCase:

    @pytest.mark.asyncio
    async def test_register_with_url_only(self, in_memory_repo, duplicate_detector, scorer):
        """Registrar un topic solo con URL debe funcionar."""
        use_case = RegisterManualInputUseCase(
            repository=in_memory_repo,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = ManualInputDTO(
            url="https://example.com/news/test",
            title="Noticia de prueba",
        )
        result = await use_case.execute(dto)

        assert result.topic.title == "Noticia de prueba"
        assert result.topic.status == "pending_review"
        assert result.topic.url == "https://example.com/news/test"
        assert result.is_duplicate is False
        assert len(result.events) > 0

    @pytest.mark.asyncio
    async def test_register_all_fields(self, in_memory_repo, duplicate_detector, scorer):
        """Registrar con todos los campos debe funcionar."""
        use_case = RegisterManualInputUseCase(
            repository=in_memory_repo,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = ManualInputDTO(
            url="https://example.com/news/full",
            title="Noticia completa",
            content="Contenido extenso de la noticia para pruebas. " * 20,
            description="Una descripción breve",
            author="Autor Test",
        )
        result = await use_case.execute(dto)

        assert result.topic.title == "Noticia completa"
        assert result.topic.author == "Autor Test"
        assert result.topic.score_total > 0

    @pytest.mark.asyncio
    async def test_register_empty_input_raises(self, in_memory_repo, duplicate_detector, scorer):
        """Input completamente vacío debe lanzar error."""
        use_case = RegisterManualInputUseCase(
            repository=in_memory_repo,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = ManualInputDTO()  # Todo None/vacío

        with pytest.raises(InvalidManualInputError):
            await use_case.execute(dto)

    @pytest.mark.asyncio
    async def test_register_duplicate_detection(self, in_memory_repo, duplicate_detector, scorer):
        """Registrar un duplicado debe marcarlo como tal."""
        # Primero registrar uno
        use_case = RegisterManualInputUseCase(
            repository=in_memory_repo,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto1 = ManualInputDTO(
            url="https://example.com/dup-test",
            title="Título duplicado",
        )
        await use_case.execute(dto1)

        # Segundo registro con misma URL
        dto2 = ManualInputDTO(
            url="https://example.com/dup-test",
            title="Otro título",
        )
        result2 = await use_case.execute(dto2)

        assert result2.is_duplicate is True


# ── ApproveTopicUseCase ──────────────────────────────


class TestApproveTopicUseCase:

    @pytest.mark.asyncio
    async def test_approve_existing_topic(self, in_memory_repo, sample_topic):
        """Aprobar un topic existente debe funcionar."""
        await in_memory_repo.save(sample_topic)

        use_case = ApproveTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=sample_topic.id)
        result = await use_case.execute(dto)

        assert result.topic.status == "approved"
        assert result.topic.reviewed_at is not None
        assert len(result.events) >= 1
        assert result.events[0]["type"] == "TopicApproved"

    @pytest.mark.asyncio
    async def test_approve_nonexistent_topic_raises(self, in_memory_repo):
        """Aprobar un topic que no existe debe lanzar error."""
        use_case = ApproveTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=uuid4())

        with pytest.raises(ResearchTopicNotFoundError):
            await use_case.execute(dto)

    @pytest.mark.asyncio
    async def test_approve_already_approved_raises(self, in_memory_repo, approved_topic):
        """Aprobar un topic ya aprobado debe lanzar error."""
        await in_memory_repo.save(approved_topic)

        use_case = ApproveTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=approved_topic.id)

        with pytest.raises(ResearchAlreadyReviewedError):
            await use_case.execute(dto)


# ── RejectTopicUseCase ───────────────────────────────


class TestRejectTopicUseCase:

    @pytest.mark.asyncio
    async def test_reject_existing_topic(self, in_memory_repo, sample_topic):
        """Rechazar un topic existente debe funcionar."""
        await in_memory_repo.save(sample_topic)

        use_case = RejectTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=sample_topic.id, reject_reason="No relevante")
        result = await use_case.execute(dto)

        assert result.topic.status == "rejected"
        assert result.topic.reviewed_at is not None
        assert len(result.events) >= 1
        assert result.events[0]["type"] == "TopicRejected"

    @pytest.mark.asyncio
    async def test_reject_nonexistent_topic_raises(self, in_memory_repo):
        use_case = RejectTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=uuid4())

        with pytest.raises(ResearchTopicNotFoundError):
            await use_case.execute(dto)

    @pytest.mark.asyncio
    async def test_reject_already_rejected_raises(self, in_memory_repo, rejected_topic):
        await in_memory_repo.save(rejected_topic)

        use_case = RejectTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=rejected_topic.id)

        with pytest.raises(ResearchAlreadyReviewedError):
            await use_case.execute(dto)


# ── ListTopicsUseCase ────────────────────────────────


class TestListTopicsUseCase:

    @pytest.mark.asyncio
    async def test_list_empty(self, in_memory_repo):
        """Listar topics cuando no hay debe retornar lista vacía."""
        use_case = ListTopicsUseCase(repository=in_memory_repo)
        query = ListTopicsQuery()
        results = await use_case.execute(query)

        assert results == []

    @pytest.mark.asyncio
    async def test_list_all_topics(self, in_memory_repo, topics_batch):
        """Listar todos los topics."""
        await in_memory_repo.save_many(topics_batch)

        use_case = ListTopicsUseCase(repository=in_memory_repo)
        query = ListTopicsQuery(limit=50)
        results = await use_case.execute(query)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_list_by_status(self, in_memory_repo, sample_topic):
        """Listar topics filtrados por estado."""
        await in_memory_repo.save(sample_topic)

        use_case = ListTopicsUseCase(repository=in_memory_repo)
        query = ListTopicsQuery(status="pending_review")
        results = await use_case.execute(query)

        assert len(results) == 1
        assert results[0].status == "pending_review"

    @pytest.mark.asyncio
    async def test_count_by_status(self, in_memory_repo, sample_topic, approved_topic):
        """Contar topics por estado."""
        await in_memory_repo.save(sample_topic)
        await in_memory_repo.save(approved_topic)

        use_case = ListTopicsUseCase(repository=in_memory_repo)
        counts = await use_case.count_by_status()

        assert counts["pending_review"] >= 1
        assert counts["approved"] >= 1

    @pytest.mark.asyncio
    async def test_get_pending_review(self, in_memory_repo, sample_topic, approved_topic):
        """Obtener topics pendientes de revisión."""
        await in_memory_repo.save(sample_topic)
        await in_memory_repo.save(approved_topic)

        use_case = ListTopicsUseCase(repository=in_memory_repo)
        pending = await use_case.get_pending_review()

        assert len(pending) >= 1
        for t in pending:
            assert t.status == "pending_review"


# ── AutoDiscoverTopicsUseCase ────────────────────────


class TestAutoDiscoverTopicsUseCase:

    @pytest.mark.asyncio
    async def test_discover_from_mock_source(self, in_memory_repo, duplicate_detector, scorer):
        """Descubrir topics desde un mock source debe funcionar."""
        from research.application.source_registry import SourceRegistry
        from research.infrastructure.sources.mock_source import MockResearchSource

        registry = SourceRegistry()
        registry.register(MockResearchSource())

        use_case = AutoDiscoverTopicsUseCase(
            repository=in_memory_repo,
            source_registry=registry,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = AutoDiscoverDTO(query="IA", limit=3)
        result = await use_case.execute(dto)

        assert len(result.discovered) > 0
        assert len(result.errors) == 0
        # Verificar que se guardaron
        saved = await in_memory_repo.find_all()
        assert len(saved) == len(result.discovered)

    @pytest.mark.asyncio
    async def test_discover_with_no_registered_sources(self, in_memory_repo, duplicate_detector, scorer):
        """Sin fuentes registradas, no debe haber descubrimientos."""
        from research.application.source_registry import SourceRegistry

        registry = SourceRegistry()

        use_case = AutoDiscoverTopicsUseCase(
            repository=in_memory_repo,
            source_registry=registry,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = AutoDiscoverDTO(query="IA")
        result = await use_case.execute(dto)

        assert len(result.discovered) == 0

    @pytest.mark.asyncio
    async def test_discover_deduplicates(self, in_memory_repo, duplicate_detector, scorer):
        """El descubrimiento debe detectar duplicados contra existentes."""
        from research.application.source_registry import SourceRegistry
        from research.infrastructure.sources.mock_source import MockResearchSource

        # Guardar un topic que el mock source va a encontrar
        existing = ResearchTopic(
            title="Nuevo modelo de IA supera a GPT-4 en razonamiento lógico",
            url="https://example.com/ai/logicnet-supera-gpt4",
        )
        await in_memory_repo.save(existing)

        registry = SourceRegistry()
        registry.register(MockResearchSource())

        use_case = AutoDiscoverTopicsUseCase(
            repository=in_memory_repo,
            source_registry=registry,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = AutoDiscoverDTO(query="IA", limit=5)
        result = await use_case.execute(dto)

        # El topic que ya existía no debería estar en discovered
        dup_titles = [t.title for t in result.duplicates]
        dup_urls = [t.url for t in result.duplicates]
        assert existing.title in dup_titles or existing.url in dup_urls

    @pytest.mark.asyncio
    async def test_discover_source_unavailable(self, in_memory_repo, duplicate_detector, scorer):
        """Si la fuente falla en fetch, debe reportarse como error."""
        from research.application.source_registry import SourceRegistry
        from research.domain.exceptions import SourceNotAvailableError

        class FailingSource:
            """Source que siempre falla en fetch."""
            source_name = "failing-source"
            available = True

            async def fetch(self, query=None, limit=10):
                raise SourceNotAvailableError(source_name=self.source_name)

        registry = SourceRegistry()
        registry.register(FailingSource())

        use_case = AutoDiscoverTopicsUseCase(
            repository=in_memory_repo,
            source_registry=registry,
            duplicate_detector=duplicate_detector,
            scorer=scorer,
        )
        dto = AutoDiscoverDTO(query="test")
        result = await use_case.execute(dto)

        assert len(result.discovered) == 0
        assert len(result.errors) == 1
        assert result.errors[0]["source"] == "failing-source"
