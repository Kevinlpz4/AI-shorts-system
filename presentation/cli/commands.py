"""
CLI Commands — Comandos de línea de comandos
==============================================
Interfaz de usuario principal.
Usa los casos de uso, nunca llama a infraestructura directamente.
"""
import asyncio
import logging
from typing import Optional

from application.dto import (
    GenerateContentRequest,
    EvaluateRequest,
    TrendRequest,
)
from application.dto.responses import ContentResult

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
