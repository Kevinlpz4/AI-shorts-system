"""
ResearchScheduler — Servicio de descubrimiento automático programado
========================================================================
Ejecuta AutoDiscoverTopicsUseCase periódicamente según configuración.

Es un servicio de Application (orquesta), no de dominio.
Usa asyncio.Task para correr en background.

Flujo:
  1. start() → crea una tarea asyncio que itera cada N minutos
  2. En cada ciclo: ejecuta discover para cada query configurada
  3. stop() → cancela la tarea gracefulmente
  4. Config persistida vía SchedulerConfig (intervalo, queries, on/off)

Thread safety:
  - Se ejecuta en el mismo event loop que el resto de la app
  - Usar desde CLI: `await scheduler.start()` y mantener loop vivo
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from research.application.use_cases.auto_discover import AutoDiscoverTopicsUseCase
from research.application.dtos import AutoDiscoverDTO
from research.infrastructure.persistence.scheduler_config import SchedulerConfig

logger = logging.getLogger(__name__)


class ResearchScheduler:
    """
    Scheduler de descubrimiento automático.

    Arranca/detiene un loop asyncio que ejecuta descubrimiento
    cada N minutos con las queries configuradas.

    Uso:
        scheduler = ResearchScheduler(use_case, config)
        await scheduler.start()       # arranca
        await scheduler.set_interval(30)  # cambia intervalo
        await scheduler.stop()        # detiene
    """

    def __init__(
        self,
        auto_discover_use_case: AutoDiscoverTopicsUseCase,
        config: SchedulerConfig,
    ):
        self._use_case = auto_discover_use_case
        self._config = config
        self._task: Optional[asyncio.Task] = None
        self._running_query: Optional[str] = None

    # ── Propiedades ──────────────────────────────────

    @property
    def is_running(self) -> bool:
        """Si el scheduler está ejecutándose actualmente."""
        return self._task is not None and not self._task.done()

    @property
    def running_query(self) -> Optional[str]:
        """Query que se está ejecutando actualmente (None si inactivo)."""
        return self._running_query

    # ── Control de ciclo de vida ──────────────────────

    async def start(self) -> None:
        """
        Inicia el scheduler.
        Si ya está corriendo, no hace nada.
        """
        if self.is_running:
            logger.info("⏳ Scheduler ya está corriendo")
            return

        self._task = asyncio.create_task(self._run_loop())
        self._config.set_enabled(True)
        logger.info(
            "▶️ Scheduler iniciado (intervalo: %d min, queries: %s)",
            self._config.get_interval(),
            self._config.get_queries(),
        )

    async def stop(self) -> None:
        """
        Detiene el scheduler gracefulmente.
        Espera a que el ciclo actual termine si está en ejecución.
        """
        if not self.is_running:
            logger.info("⏹ Scheduler ya está detenido")
            return

        self._config.set_enabled(False)
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("⏹ Scheduler detenido")

    async def run_once(self) -> dict:
        """
        Ejecuta UN ciclo de descubrimiento ahora (sin esperar intervalo).
        Útil para CLI: `shorts research schedule run-now`

        Returns:
            Dict con discovered, duplicates, errors del ciclo ejecutado.
        """
        return await self._execute_cycle()

    # ── Configuración ─────────────────────────────────

    async def set_interval(self, minutes: int) -> None:
        """Cambia el intervalo entre ciclos (minutos)."""
        self._config.set_interval(minutes)
        logger.info("⏱ Intervalo del scheduler actualizado a %d minutos", minutes)

    async def set_queries(self, queries: list[str]) -> None:
        """Cambia las queries a ejecutar en cada ciclo."""
        self._config.set_queries(queries)
        logger.info("🔍 Queries del scheduler actualizadas: %s", queries)

    def get_status(self) -> dict:
        """Retorna estado completo del scheduler."""
        status = self._config.get_status()
        status["is_running"] = self.is_running
        status["running_query"] = self.running_query
        return status

    # ── Loop interno ──────────────────────────────────

    async def _run_loop(self) -> None:
        """Loop principal: ejecuta ciclos cada N minutos."""
        try:
            while True:
                await self._execute_cycle()
                interval = self._config.get_interval()
                logger.debug(
                    "😴 Scheduler esperando %d minutos hasta próximo ciclo",
                    interval,
                )
                await asyncio.sleep(interval * 60)
        except asyncio.CancelledError:
            logger.info("⏹ Scheduler loop cancelado")
            raise

    async def _execute_cycle(self) -> dict:
        """
        Ejecuta UN ciclo: descubre para todas las queries configuradas.

        Returns:
            Dict con discovered_count, duplicates_count, errors del ciclo.
            errors es lista de dicts con detalle, discovered/duplicates son
            conteos (los topics completos son demasiado pesados para API).
        """
        queries = self._config.get_queries()
        logger.info(
            "🔄 Scheduler ejecutando ciclo con %d queries",
            len(queries),
        )

        total_discovered = 0
        total_duplicates = 0
        all_errors: list[dict] = []

        for query in queries:
            self._running_query = query
            try:
                result = await self._use_case.execute(
                    AutoDiscoverDTO(query=query, limit=5)
                )
                total_discovered += len(result.discovered)
                total_duplicates += len(result.duplicates)
                if result.errors:
                    all_errors.extend(result.errors)
                    for err in result.errors:
                        logger.warning(
                            "⚠️ [Scheduler] Error en fuente '%s': %s",
                            err.get("source", "?"),
                            err.get("error", "?"),
                        )
                logger.info(
                    "   📥 Query '%s': %d nuevos, %d duplicados",
                    query,
                    len(result.discovered),
                    len(result.duplicates),
                )
            except Exception as e:
                logger.exception(
                    "❌ [Scheduler] Error ejecutando query '%s': %s",
                    query,
                    e,
                )
                all_errors.append(
                    {"query": query, "error": str(e)}
                )

        self._running_query = None
        self._config.set_last_run(
            datetime.now(timezone.utc).isoformat()
        )

        logger.info(
            "✅ Ciclo completado: %d descubiertos, %d duplicados, %d errores",
            total_discovered,
            total_duplicates,
            len(all_errors),
        )

        return {
            "discovered_count": total_discovered,
            "duplicates_count": total_duplicates,
            "errors": all_errors,
        }
