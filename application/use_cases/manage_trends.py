import logging
from typing import Optional

from domain.entities.trend import Trend
from domain.ports.trend_source import TrendSourcePort
from domain.ports.content_repository import ContentRepository
from domain.ports.cache import CachePort
from domain.exceptions.trends import TrendNotFoundError
from application.dto import TrendRequest
from application.dto.responses import ContentResult

logger = logging.getLogger(__name__)


class ManageTrendsUseCase:
    """
    Caso de uso: OBTENER Y GESTIONAR TENDENCIAS.
    
    Consulta múltiples fuentes y consolida resultados.
    """
    
    def __init__(
        self,
        sources: list[TrendSourcePort],
        repository: ContentRepository,
        cache: CachePort,
    ):
        self._sources = sources
        self._repo = repository
        self._cache = cache

    async def execute(self, request: TrendRequest) -> ContentResult:
        """Obtiene tendencias de todas las fuentes."""
        try:
            cache_key = f"trends:{request.niche or 'general'}:{','.join(request.sources)}"
            cached = self._cache.get(cache_key)
            if cached:
                logger.info(f"💾 Trends desde cache ({len(cached)} items)")
                return ContentResult.ok(data={"trends": cached})

            all_trends = []
            for source in self._sources:
                try:
                    if source.available:
                        trends = await source.fetch_trends(
                            niche=request.niche,
                            limit=request.limit,
                        )
                        all_trends.extend(trends)
                        logger.info(f"📡 {source.source_name}: {len(trends)} trends")
                except Exception as e:
                    logger.warning(f"⚠️ {source.source_name}: {e}")

            if not all_trends:
                return ContentResult.ok(
                    data={"trends": [], "message": "No hay tendencias disponibles"},
                )

            # Ordenar por viral score
            all_trends.sort(key=lambda t: int(t.viral_score), reverse=True)
            top_trends = all_trends[:request.limit]

            # Cachear
            trends_dicts = [t.to_dict() for t in top_trends]
            self._cache.set(cache_key, trends_dicts)

            logger.info(f"✅ {len(top_trends)} trends obtenidos")
            return ContentResult.ok(data={"trends": trends_dicts})

        except Exception as e:
            logger.error(f"Error obteniendo trends: {e}")
            return ContentResult.error(str(e))
