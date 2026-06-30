"""
Tests para escenarios de auto_generate en ApproveTopicUseCase.
================================================================
Cubre las 5 variantes definidas en la spec:
  - auto_generate=True → genera script
  - auto_generate=None y config enabled → genera script
  - auto_generate=None y config disabled → NO genera
  - auto_generate=False → NO genera (backward compat)
  - Ya existe script → skip
  - Falla generación → no revierte approve
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from uuid import uuid4

from research.application.dtos import ReviewDecisionDTO, ReviewResultDTO
from research.application.use_cases.approve_topic import ApproveTopicUseCase
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_source import ResearchSource
from research.domain.entities.research_topic import ResearchTopic


# ── Fixtures ───────────────────────────────────────────


@pytest.fixture
def sample_topic_pending() -> ResearchTopic:
    """Topic en PENDING_REVIEW para usar en tests."""
    return ResearchTopic(
        title="Topic para aprobar",
        description="Descripción de prueba",
        content="Contenido de prueba para el topic. " * 10,
        source=ResearchSource.google_news(),
        score=ResearchScore(relevance=80, popularity=70, recency=60, source_reliability=90),
    )


@pytest.fixture
def mock_generate_script_uc():
    """Mock de GenerateScriptUseCase."""
    uc = AsyncMock()
    uc.execute = AsyncMock()
    return uc


@pytest.fixture
def mock_script_repo_no_script():
    """Mock de script repository que retorna None (no existe script)."""
    repo = MagicMock()
    repo.find_by_topic_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_script_repo_with_script():
    """Mock de script repository que retorna un script existente."""
    repo = MagicMock()
    repo.find_by_topic_id = AsyncMock(return_value=MagicMock(id="script-123"))
    return repo


@pytest.fixture
def mock_scheduler_config_enabled():
    """Mock de SchedulerConfig con auto_generate habilitado."""
    cfg = MagicMock()
    cfg.is_auto_generate_enabled = MagicMock(return_value=True)
    return cfg


@pytest.fixture
def mock_scheduler_config_disabled():
    """Mock de SchedulerConfig con auto_generate deshabilitado."""
    cfg = MagicMock()
    cfg.is_auto_generate_enabled = MagicMock(return_value=False)
    return cfg


@pytest.fixture
def in_memory_repo():
    """Repositorio simple en memoria para los tests."""
    class InMemoryRepo:
        def __init__(self):
            self._topics = {}

        async def save(self, topic):
            self._topics[str(topic.id)] = topic

        async def find_by_id(self, topic_id):
            return self._topics.get(str(topic_id))

    return InMemoryRepo()


# ── Tests ──────────────────────────────────────────────


class TestApproveTopicAutoGenerate:

    @pytest.mark.asyncio
    async def test_approve_without_auto_generate(
        self, in_memory_repo, sample_topic_pending,
    ):
        """auto_generate no especificado → solo aprueba (backward compat)."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto)

        assert result.topic.status == "approved"
        assert len(result.events) >= 1
        assert result.events[0]["type"] == "TopicApproved"

    @pytest.mark.asyncio
    async def test_approve_with_auto_generate_false(
        self, in_memory_repo, sample_topic_pending,
        mock_generate_script_uc, mock_script_repo_no_script,
        mock_scheduler_config_enabled,
    ):
        """auto_generate=False explícito → no genera script (pisa config)."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=mock_generate_script_uc,
            script_repo=mock_script_repo_no_script,
            scheduler_config=mock_scheduler_config_enabled,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=False)

        assert result.topic.status == "approved"
        mock_generate_script_uc.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_with_auto_generate_true(
        self, in_memory_repo, sample_topic_pending,
        mock_generate_script_uc, mock_script_repo_no_script,
    ):
        """auto_generate=True → genera script."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=mock_generate_script_uc,
            script_repo=mock_script_repo_no_script,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=True)

        assert result.topic.status == "approved"
        mock_generate_script_uc.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_with_auto_generate_enabled_config(
        self, in_memory_repo, sample_topic_pending,
        mock_generate_script_uc, mock_script_repo_no_script,
        mock_scheduler_config_enabled,
    ):
        """auto_generate=None + config enabled → genera script."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=mock_generate_script_uc,
            script_repo=mock_script_repo_no_script,
            scheduler_config=mock_scheduler_config_enabled,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=None)

        assert result.topic.status == "approved"
        mock_generate_script_uc.execute.assert_awaited_once()
        mock_scheduler_config_enabled.is_auto_generate_enabled.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_with_auto_generate_disabled_config(
        self, in_memory_repo, sample_topic_pending,
        mock_generate_script_uc, mock_script_repo_no_script,
        mock_scheduler_config_disabled,
    ):
        """auto_generate=None + config disabled → NO genera script."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=mock_generate_script_uc,
            script_repo=mock_script_repo_no_script,
            scheduler_config=mock_scheduler_config_disabled,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=None)

        assert result.topic.status == "approved"
        mock_generate_script_uc.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_auto_generate_skips_existing_script(
        self, in_memory_repo, sample_topic_pending,
        mock_generate_script_uc, mock_script_repo_with_script,
    ):
        """auto_generate=True pero ya existe script → skip."""
        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=mock_generate_script_uc,
            script_repo=mock_script_repo_with_script,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=True)

        assert result.topic.status == "approved"
        # No debe llamar a generate porque ya existe script
        mock_generate_script_uc.execute.assert_not_called()
        mock_script_repo_with_script.find_by_topic_id.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_auto_generate_failure_does_not_revert(
        self, in_memory_repo, sample_topic_pending,
        mock_script_repo_no_script,
    ):
        """auto_generate falla → log error, approve NO se revierte."""
        failing_uc = AsyncMock()
        failing_uc.execute = AsyncMock(side_effect=RuntimeError("API timeout"))

        await in_memory_repo.save(sample_topic_pending)
        use_case = ApproveTopicUseCase(
            repository=in_memory_repo,
            generate_script_uc=failing_uc,
            script_repo=mock_script_repo_no_script,
        )
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        # No debe lanzar excepción — el error se loggea internamente
        result = await use_case.execute(dto, auto_generate=True)

        assert result.topic.status == "approved"
        failing_uc.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_approve_auto_generate_no_deps_configured(
        self, in_memory_repo, sample_topic_pending,
    ):
        """auto_generate=True pero sin generate_script_uc → log warning, no error."""
        await in_memory_repo.save(sample_topic_pending)
        # Sin generate_script_uc ni script_repo
        use_case = ApproveTopicUseCase(repository=in_memory_repo)
        dto = ReviewDecisionDTO(topic_id=sample_topic_pending.id)

        result = await use_case.execute(dto, auto_generate=True)

        assert result.topic.status == "approved"
