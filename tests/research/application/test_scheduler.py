"""
Tests unitarios para ResearchScheduler (servicio de descubrimiento automático).
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research.application.scheduler import ResearchScheduler
from research.application.dtos import (
    AutoDiscoverDTO,
    DiscoverBatchResultDTO,
    ResearchTopicDTO,
)
from research.infrastructure.persistence.scheduler_config import SchedulerConfig


class TestResearchScheduler:
    """ResearchScheduler con mocks."""

    @pytest.fixture
    def config(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        sc = SchedulerConfig(db_path=db_path)
        yield sc
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def use_case(self):
        """Mock de AutoDiscoverTopicsUseCase."""
        uc = AsyncMock()
        uc.execute.return_value = DiscoverBatchResultDTO(
            discovered=[
                ResearchTopicDTO(
                    id="00000000-0000-0000-0000-000000000001",
                    title="Test Topic",
                    description="",
                    content_preview="",
                    source_name="mock",
                    source_type="automatic",
                    status="pending_review",
                    score_total=65.0,
                    score_components={},
                    url="https://example.com",
                    author=None,
                    created_at=None,
                    reviewed_at=None,
                )
            ],
            duplicates=[],
            errors=[],
        )
        return uc

    @pytest.fixture
    def scheduler(self, use_case, config):
        return ResearchScheduler(auto_discover_use_case=use_case, config=config)

    # ── Estado inicial ──────────────────────────────

    def test_initial_not_running(self, scheduler: ResearchScheduler):
        """Scheduler debe empezar detenido."""
        assert scheduler.is_running is False
        assert scheduler.running_query is None

    def test_initial_status(self, scheduler: ResearchScheduler):
        """get_status debe reflejar estado inicial."""
        status = scheduler.get_status()
        assert status["is_running"] is False
        assert status["enabled"] is False

    # ── Start / Stop ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_start(self, scheduler: ResearchScheduler):
        """start debe poner is_running en True."""
        await scheduler.start()
        assert scheduler.is_running is True
        # Verificar que persistió enabled=True
        assert scheduler._config.is_enabled() is True

    @pytest.mark.asyncio
    async def test_stop(self, scheduler: ResearchScheduler):
        """stop debe poner is_running en False."""
        await scheduler.start()
        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler._config.is_enabled() is False

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, scheduler: ResearchScheduler):
        """stop sin haber arrancado no debe fallar."""
        await scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_start_twice(self, scheduler: ResearchScheduler):
        """start dos veces no debe crear tareas duplicadas."""
        await scheduler.start()
        task_1 = scheduler._task
        await scheduler.start()  # No hace nada
        task_2 = scheduler._task
        assert task_1 is task_2  # Misma tarea
        await scheduler.stop()

    # ── Run Once ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_run_once(self, scheduler: ResearchScheduler, use_case, config):
        """run_once debe ejecutar el use case para cada query."""
        config.set_queries(["test-query"])
        await scheduler.run_once()
        use_case.execute.assert_awaited_once()
        args, _ = use_case.execute.call_args
        assert isinstance(args[0], AutoDiscoverDTO)
        assert args[0].query == "test-query"

    @pytest.mark.asyncio
    async def test_run_once_with_config_queries(
        self, scheduler: ResearchScheduler, use_case, config
    ):
        """run_once debe usar las queries de la config."""
        config.set_queries(["test-query"])
        await scheduler.run_once()
        use_case.execute.assert_awaited_once()
        assert use_case.execute.call_args[0][0].query == "test-query"

    # ── Set Interval ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_set_interval(self, scheduler: ResearchScheduler, config):
        """set_interval debe persistir el cambio."""
        await scheduler.set_interval(30)
        assert config.get_interval() == 30

    @pytest.mark.asyncio
    async def test_set_interval_minimum(self, scheduler: ResearchScheduler, config):
        """set_interval con valor inválido debe fallar gracefulmente."""
        await scheduler.set_interval(0)
        assert config.get_interval() >= 1

    # ── Set Queries ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_set_queries(self, scheduler: ResearchScheduler, config):
        """set_queries debe persistir el cambio."""
        await scheduler.set_queries(["a", "b", "c"])
        assert config.get_queries() == ["a", "b", "c"]

    # ── Run Once con errores ─────────────────────────

    @pytest.mark.asyncio
    async def test_run_once_use_case_error(self, scheduler: ResearchScheduler, use_case):
        """Si el use case falla, run_once no debe propagar error."""
        use_case.execute.side_effect = RuntimeError("API Error")
        # No debe lanzar
        await scheduler.run_once()

    @pytest.mark.asyncio
    async def test_run_once_partial_errors(self, use_case, config):
        """Resultado con errores parciales no debe fallar."""
        use_case.execute.return_value = DiscoverBatchResultDTO(
            discovered=[],
            duplicates=[],
            errors=[{"source": "google-news", "error": "Timeout"}],
        )
        scheduler = ResearchScheduler(auto_discover_use_case=use_case, config=config)
        await scheduler.run_once()
        # No debe lanzar excepción

    # ── Status ───────────────────────────────────────

    def test_get_status_reflects_config(self, scheduler: ResearchScheduler, config):
        """get_status debe reflejar cambios en config."""
        config.set_interval(15)
        config.set_queries(["custom"])
        status = scheduler.get_status()
        assert status["interval_minutes"] == 15
        assert status["queries"] == ["custom"]

    # ── Lifecycle completo ───────────────────────────

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, scheduler: ResearchScheduler):
        """Start → run_once → stop debe funcionar correctamente."""
        assert scheduler.is_running is False

        await scheduler.start()
        assert scheduler.is_running is True
        assert scheduler._config.is_enabled() is True

        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler._config.is_enabled() is False

    # ── Loop ejecuta ciclo y espera ──────────────────

    @pytest.mark.asyncio
    async def test_loop_executes_and_waits(self, use_case, config):
        """El loop debe ejecutar el use case y luego esperar."""
        config.set_interval(99999)  # Intervalo enorme para que no ejecute otro

        # Un mock que duerme un poco y permite cancelación limpia
        real_sleep = asyncio.sleep

        async def controlled_sleep(duration):
            """Pequeña pausa para dar chance a cancel."""
            await real_sleep(0.05)

        scheduler = ResearchScheduler(auto_discover_use_case=use_case, config=config)

        with patch("asyncio.sleep", controlled_sleep):
            # Arrancar y dar tiempo para que ejecute al menos un ciclo
            await scheduler.start()
            await real_sleep(0.1)

            # Verificar que se ejecutó al menos una vez
            assert use_case.execute.awaited

            # Detener
            await scheduler.stop()

        assert scheduler.is_running is False

    # ── Múltiples queries ────────────────────────────

    @pytest.mark.asyncio
    async def test_loop_multiple_queries(self, use_case, config):
        """El loop debe ejecutar todas las queries configuradas."""
        config.set_queries(["q1", "q2", "q3"])
        config.set_interval(99999)

        scheduler = ResearchScheduler(auto_discover_use_case=use_case, config=config)

        # Simular solo un ciclo
        await scheduler.run_once()

        # Debe haber ejecutado 3 queries
        assert use_case.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_loop_records_last_run(self, use_case, config):
        """Después de ejecutar, debe actualizar last_run."""
        scheduler = ResearchScheduler(auto_discover_use_case=use_case, config=config)
        assert config.get_last_run() is None

        await scheduler.run_once()
        assert config.get_last_run() is not None
