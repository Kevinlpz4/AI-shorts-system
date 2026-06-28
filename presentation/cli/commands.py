"""
CLI Commands — Comandos de línea de comandos
==============================================
Interfaz de usuario principal.
Usa los casos de uso, nunca llama a infraestructura directamente.
"""
import asyncio
import logging
from typing import Optional
from uuid import UUID

from application.dto import (
    GenerateContentRequest,
    EvaluateRequest,
    TrendRequest,
)
from application.dto.responses import ContentResult

from research.application.dtos import (
    AutoDiscoverDTO,
    RegisterManualDTO,
    ApproveDTO,
    RejectDTO,
    ListTopicsDTO,
)
from research.domain.value_objects.research_status import ResearchStatus

logger = logging.getLogger(__name__)


class CLICommands:
    """
    Comandos CLI que usa los casos de uso.
    
    NO sabe de infraestructura.
    NO sabe de domains directamente.
    Solo llama a use cases.
    """
    
    def __init__(self, container):
        self._container = container

    async def run_generate(
        self,
        niche: Optional[str] = None,
        platform: str = "youtube",
        count: int = 1,
    ) -> ContentResult:
        """Comando: generar contenido."""
        logger.info(f"🎬 Generando {count} video(s) para {platform}")

        request = GenerateContentRequest(
            niche=niche,
            platform=platform,
            count=count,
        )

        for i in range(count):
            logger.info(f"\n{'='*50}")
            logger.info(f"Video {i+1}/{count}")
            logger.info(f"{'='*50}")

            result = await self._container.generate_content.execute(request)

            if result.success:
                data = result.data or {}
                logger.info(f"   ✅ Idea: {data.get('idea', {}).get('hook', 'N/A')[:60]}...")
                logger.info(f"   📊 Score: {data.get('idea', {}).get('viral_score', 'N/A')}")
                
                if data.get('publish'):
                    logger.info(f"   🚀 Publicado: {data['publish'].get('url', 'N/A')}")
            else:
                logger.error(f"   ❌ {result.message}")

        return result

    async def run_trends(
        self,
        niche: Optional[str] = None,
        limit: int = 20,
    ) -> ContentResult:
        """Comando: obtener tendencias."""
        logger.info(f"📡 Obteniendo trends (niche: {niche or 'general'})")

        request = TrendRequest(niche=niche, limit=limit)
        result = await self._container.manage_trends.execute(request)

        if result.success and result.data:
            trends = result.data.get("trends", [])
            logger.info(f"✅ {len(trends)} trends obtenidos")
            for i, trend in enumerate(trends[:5], 1):
                logger.info(f"   {i}. {trend.get('topic', 'N/A')} (score: {trend.get('viral_score', 'N/A')})")

        return result

    async def run_evaluate(
        self,
        content_id: str,
        content_type: str = "idea",
    ) -> ContentResult:
        """Comando: evaluar contenido."""
        logger.info(f"📊 Evaluando {content_type}: {content_id}")

        request = EvaluateRequest(
            content_type=content_type,
            content_id=content_id,
            optimize=True,
        )
        result = await self._container.evaluate_content.execute(request)

        if result.success and result.data:
            eval_data = result.data.get("evaluation", {})
            logger.info(f"   Score: {eval_data.get('score', 'N/A')}/10")
            logger.info(f"   Clasificación: {eval_data.get('classification', 'N/A')}")
            if eval_data.get("recommendations"):
                for rec in eval_data["recommendations"]:
                    logger.info(f"   💡 {rec}")

        return result

    # ═══════════════════════════════════════════════
    # Research Commands
    # ═══════════════════════════════════════════════

    async def research_discover(
        self,
        query: Optional[str] = None,
        limit: int = 5,
        sources: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Comando: descubrir topics desde fuentes externas.

        Args:
            query: Término de búsqueda (None = trending)
            limit: Máximo de resultados por fuente
            sources: Fuentes específicas (None = todas disponibles)

        Returns:
            Lista de topics descubiertos como dicts
        """
        logger.info(f"🔍 Descubriendo topics (query: {query or 'trending'})")

        dto = AutoDiscoverDTO(query=query, limit=limit, source_names=sources)
        result = await self._container.auto_discover_topics.execute(dto)

        discovered = [t.model_dump() for t in result.discovered]
        duplicates = [t.model_dump() for t in result.duplicates]

        logger.info(f"✅ {len(discovered)} topics descubiertos")
        if duplicates:
            logger.info(f"⚠️ {len(duplicates)} duplicados ignorados")
        if result.errors:
            for err in result.errors:
                logger.warning(f"   ⚠️ {err.get('source')}: {err.get('error')}")

        for t in discovered:
            logger.info(
                "   📰 %s (score: %.1f, fuente: %s)",
                t["title"][:60],
                t["score_total"],
                t["source_name"],
            )

        return discovered

    async def research_list(
        self,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Comando: listar topics existentes.

        Args:
            status: Filtrar por estado (pending_review, approved, rejected)
            limit: Máximo de resultados

        Returns:
            Lista de topics como dicts
        """
        status_filter = None
        if status:
            try:
                status_filter = ResearchStatus(status)
            except ValueError:
                valid = [s.value for s in ResearchStatus]
                logger.error(f"❌ Estado inválido: {status}. Válidos: {valid}")
                return []

        dto = ListTopicsDTO(status=status_filter, limit=limit)
        result = await self._container.list_topics.execute(dto)

        topics = [t.model_dump() for t in result.topics]
        logger.info(f"📋 {len(topics)} topics encontrados")

        for t in topics:
            status_icon = {
                "pending_review": "⏳",
                "approved": "✅",
                "rejected": "❌",
            }.get(t["status"], "📄")
            logger.info(
                "   %s %s | score: %.1f | %s | %s",
                status_icon,
                str(t["id"])[:8],
                t["score_total"],
                t["status"],
                t["title"][:60],
            )

        return topics

    async def research_approve(self, topic_id: str) -> Optional[dict]:
        """
        Comando: aprobar un topic para generación.

        Args:
            topic_id: UUID del topic

        Returns:
            Topic actualizado como dict, o None si no existe
        """
        try:
            uid = UUID(topic_id)
        except ValueError:
            logger.error(f"❌ ID inválido: {topic_id}. Debe ser un UUID válido.")
            return None

        logger.info(f"✅ Aprobando topic: {topic_id}")
        dto = ApproveDTO(topic_id=uid)
        result = await self._container.approve_topic.execute(dto)

        if result.topic:
            data = result.topic.model_dump()
            logger.info("   ✅ Topic aprobado: %s", data["title"][:60])
            return data
        else:
            logger.error(f"❌ Topic no encontrado: {topic_id}")
            return None

    async def research_reject(self, topic_id: str) -> Optional[dict]:
        """
        Comando: rechazar un topic.

        Args:
            topic_id: UUID del topic

        Returns:
            Topic actualizado como dict, o None si no existe
        """
        try:
            uid = UUID(topic_id)
        except ValueError:
            logger.error(f"❌ ID inválido: {topic_id}. Debe ser un UUID válido.")
            return None

        logger.info(f"❌ Rechazando topic: {topic_id}")
        dto = RejectDTO(topic_id=uid)
        result = await self._container.reject_topic.execute(dto)

        if result.topic:
            data = result.topic.model_dump()
            logger.info("   ❌ Topic rechazado: %s", data["title"][:60])
            return data
        else:
            logger.error(f"❌ Topic no encontrado: {topic_id}")
            return None

    async def research_manual(
        self,
        title: str,
        url: str,
        description: str = "",
    ) -> Optional[dict]:
        """
        Comando: registrar un topic manualmente.

        Args:
            title: Título del topic
            url: URL de la fuente
            description: Descripción opcional

        Returns:
            Topic creado como dict, o None si es duplicado
        """
        logger.info(f"📝 Registrando topic manual: {title}")

        dto = RegisterManualDTO(title=title, url=url, description=description)
        result = await self._container.register_manual_input.execute(dto)

        if result.topic:
            data = result.topic.model_dump()
            if result.is_duplicate:
                logger.warning(
                    "   ⚠️ Topic marcado como posible duplicado: %s",
                    data["title"][:60],
                )
            else:
                logger.info("   ✅ Topic registrado: %s", data["title"][:60])
            return data
        else:
            logger.warning("   ⚠️ Topic duplicado, no se registró")
            return None

    async def research_schedule_status(self) -> dict:
        """Muestra el estado del scheduler."""
        status = self._container.research_scheduler.get_status()
        logger.info("⏱ Estado del scheduler:")
        logger.info(f"   Activo: {'✅ Sí' if status['is_running'] else '❌ No'}")
        logger.info(f"   Habilitado: {'✅ Sí' if status['enabled'] else '❌ No'}")
        logger.info(f"   Intervalo: {status['interval_minutes']} minutos")
        logger.info(f"   Queries: {', '.join(status['queries'])}")
        logger.info(f"   Última ejecución: {status.get('last_run', 'Nunca')}")
        return status

    async def research_schedule_start(self) -> None:
        """Inicia el scheduler."""
        logger.info("▶️ Iniciando scheduler...")
        await self._container.research_scheduler.start()
        logger.info("✅ Scheduler iniciado")

    async def research_schedule_stop(self) -> None:
        """Detiene el scheduler."""
        logger.info("⏹ Deteniendo scheduler...")
        await self._container.research_scheduler.stop()
        logger.info("⏹ Scheduler detenido")

    async def research_schedule_interval(self, minutes: int) -> None:
        """Cambia el intervalo del scheduler."""
        await self._container.research_scheduler.set_interval(minutes)
        logger.info(f"⏱ Intervalo actualizado a {minutes} minutos")

    async def research_schedule_queries(self, queries: list[str]) -> None:
        """Cambia las queries del scheduler."""
        await self._container.research_scheduler.set_queries(queries)
        logger.info(f"🔍 Queries actualizadas: {queries}")

    async def research_schedule_run_now(self) -> list[dict]:
        """Ejecuta un ciclo de descubrimiento inmediatamente."""
        logger.info("⚡ Ejecutando ciclo ahora...")
        await self._container.research_scheduler.run_once()
        # Mostrar los últimos topics descubiertos
        return await self.research_list(status="pending_review", limit=5)
