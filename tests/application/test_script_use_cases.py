"""
Tests para Script Use Cases (Generate, Get, Regenerate).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from application.dtos.script import GenerateScriptRequest, ScriptDTO
from application.use_cases.script.generate_script import GenerateScriptUseCase
from application.use_cases.script.get_script import GetScriptUseCase
from application.use_cases.script.regenerate_script import RegenerateScriptUseCase
from domain.entities.script import Script
from domain.exceptions.content import ScriptValidationError
from domain.exceptions.script import ScriptAlreadyExistsError
from research.domain.exceptions import ResearchTopicNotFoundError
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.value_objects.research_score import ResearchScore


# ── Helpers ───────────────────────────────────────────


def make_mock_topic(
    title="Test topic",
    status=ResearchStatus.APPROVED,
    score_total=75,
):
    """Crea un ResearchTopic mock con los campos necesarios."""
    topic = MagicMock()
    topic.id = uuid4()
    topic.title = title
    topic.description = "Test description"
    topic.content = "Test content"
    topic.status = status

    # Score con total
    score = MagicMock()
    score.total = score_total
    score.relevance = 80
    score.popularity = 70
    score.recency = 60
    score.source_reliability = 90
    topic.score = score

    return topic


def make_mock_ai_provider(valid_script=True):
    """Crea un ScriptGeneratorPort mock."""
    ai = AsyncMock()
    ai.generate_script = AsyncMock(return_value=Script(
        hook="Un hook largo que cumple el mínimo" if valid_script else "corto",
        body=("x" * 50) if valid_script else "corto",
        cta="seguime ahora" if valid_script else "x",
    ))
    return ai


# ── GetScriptUseCase ──────────────────────────────────


class TestGetScriptUseCase:

    @pytest.mark.asyncio
    async def test_get_existing_script(self):
        """Obtener un script existente debe retornar ScriptDTO."""
        script_repo = AsyncMock()
        script = Script(
            topic_id="topic-1",
            hook="Hook largo válido",
            body="x" * 50,
            cta="seguime",
        )
        script_repo.find_by_topic_id = AsyncMock(return_value=script)

        use_case = GetScriptUseCase(script_repo=script_repo)
        result = await use_case.execute("topic-1")

        assert result is not None
        assert isinstance(result, ScriptDTO)
        assert result.topic_id == "topic-1"
        assert result.is_valid is True
        script_repo.find_by_topic_id.assert_called_once_with("topic-1")

    @pytest.mark.asyncio
    async def test_get_nonexistent_script(self):
        """Obtener un script que no existe debe retornar None."""
        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        use_case = GetScriptUseCase(script_repo=script_repo)
        result = await use_case.execute("topic-not-exists")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_script_calls_repo_correctly(self):
        """Debe llamar al repo con el topic_id exacto."""
        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        use_case = GetScriptUseCase(script_repo=script_repo)
        await use_case.execute("exact-topic-id")

        script_repo.find_by_topic_id.assert_called_once_with("exact-topic-id")


# ── GenerateScriptUseCase ─────────────────────────────


class TestGenerateScriptUseCase:

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Generar guion para topic aprobado debe funcionar."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)
        script_repo.save = AsyncMock()

        ai_provider = make_mock_ai_provider(valid_script=True)

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))
        result = await use_case.execute(request)

        assert result is not None
        assert isinstance(result, ScriptDTO)
        assert result.topic_id == str(topic.id)
        assert result.is_valid is True
        script_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_topic_not_found(self):
        """Topic inexistente debe lanzar ResearchTopicNotFoundError."""
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=None)

        script_repo = AsyncMock()
        ai_provider = make_mock_ai_provider()

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(uuid4()))

        with pytest.raises(ResearchTopicNotFoundError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_generate_topic_not_approved(self):
        """Topic no aprobado debe lanzar ContentError."""
        topic = make_mock_topic(status=ResearchStatus.PENDING_REVIEW)
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        ai_provider = make_mock_ai_provider()

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))

        from domain.exceptions.content import ContentError
        with pytest.raises(ContentError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_generate_already_exists(self):
        """Script ya existente debe lanzar ScriptAlreadyExistsError."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        existing_script = Script(topic_id=str(topic.id))
        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=existing_script)

        ai_provider = make_mock_ai_provider()

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))

        with pytest.raises(ScriptAlreadyExistsError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_generate_validation_failure(self):
        """Guion inválido debe lanzar ScriptValidationError."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)
        script_repo.save = AsyncMock()

        ai_provider = make_mock_ai_provider(valid_script=False)

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))

        with pytest.raises(ScriptValidationError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_generate_rejected_topic(self):
        """Topic rechazado debe lanzar ContentError."""
        topic = make_mock_topic(status=ResearchStatus.REJECTED)
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        ai_provider = make_mock_ai_provider()

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))

        from domain.exceptions.content import ContentError
        with pytest.raises(ContentError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_generate_sets_topic_id_and_tone(self):
        """El script generado debe tener topic_id y tone asignados."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        # Capturar lo que se guarda
        saved_scripts = []

        async def capture_save(script):
            saved_scripts.append(script)

        script_repo.save = capture_save

        ai_provider = make_mock_ai_provider(valid_script=True)

        use_case = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id), tone="humor")
        await use_case.execute(request)

        assert len(saved_scripts) == 1
        assert saved_scripts[0].topic_id == str(topic.id)
        assert saved_scripts[0].tone == "humor"


# ── RegenerateScriptUseCase ───────────────────────────


class TestRegenerateScriptUseCase:

    @pytest.mark.asyncio
    async def test_regenerate_existing_script(self):
        """Regenerar debe eliminar el existente y generar uno nuevo."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        # Primera llamada: existe un script
        existing = Script(topic_id=str(topic.id))
        # Segunda llamada (desde generate): no existe (ya se borró)
        script_repo.find_by_topic_id = AsyncMock(side_effect=[existing, None])
        script_repo.delete_by_topic_id = AsyncMock()
        script_repo.save = AsyncMock()

        ai_provider = make_mock_ai_provider(valid_script=True)

        generate_uc = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        use_case = RegenerateScriptUseCase(
            script_repo=script_repo,
            generate_uc=generate_uc,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id), tone="humor")
        result = await use_case.execute(request)

        assert result is not None
        assert isinstance(result, ScriptDTO)
        script_repo.delete_by_topic_id.assert_called_once_with(str(topic.id))
        script_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_no_existing_script(self):
        """Regenerar sin script existente debe crear uno nuevo (sin eliminar)."""
        topic = make_mock_topic()
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=topic)

        script_repo = AsyncMock()
        # No hay script existente
        script_repo.find_by_topic_id = AsyncMock(return_value=None)
        script_repo.delete_by_topic_id = AsyncMock()
        script_repo.save = AsyncMock()

        ai_provider = make_mock_ai_provider(valid_script=True)

        generate_uc = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        use_case = RegenerateScriptUseCase(
            script_repo=script_repo,
            generate_uc=generate_uc,
        )
        request = GenerateScriptRequest(topic_id=str(topic.id))
        result = await use_case.execute(request)

        assert result is not None
        # delete_by_topic_id NO debe llamarse si no existía
        script_repo.delete_by_topic_id.assert_not_called()
        # save debe llamarse con el nuevo script
        script_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_topic_not_found(self):
        """Regenerar con topic inexistente debe propagar error de generate."""
        research_repo = AsyncMock()
        research_repo.find_by_id = AsyncMock(return_value=None)

        script_repo = AsyncMock()
        script_repo.find_by_topic_id = AsyncMock(return_value=None)

        ai_provider = make_mock_ai_provider()

        generate_uc = GenerateScriptUseCase(
            research_repo=research_repo,
            script_repo=script_repo,
            ai_provider=ai_provider,
        )
        use_case = RegenerateScriptUseCase(
            script_repo=script_repo,
            generate_uc=generate_uc,
        )
        request = GenerateScriptRequest(topic_id=str(uuid4()))

        with pytest.raises(ResearchTopicNotFoundError):
            await use_case.execute(request)
