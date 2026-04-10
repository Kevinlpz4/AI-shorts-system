"""
Trends Pipeline - Pipeline de Tendencias
=========================================
Pipeline para obtener solo tendencias (sin generación de contenido).
"""

import asyncio
from typing import Optional, Dict, Any, List

from app.config import settings
from app.logger import logger

from modules.trends import TrendsAnalyzer


class TrendsPipeline:
    """
    Pipeline para obtener tendencias.
    
    Útil para:
    - Debugging
    - Testing de sources
    - Preview de trends
    """
    
    def __init__(self, niche: Optional[str] = None):
        """
        Inicializa el pipeline de trends.
        
        Args:
            niche: Nicho específico
        """
        self.niche = niche
        self.trends_analyzer = TrendsAnalyzer()
    
    async def run(
        self,
        sources: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta el pipeline de trends.
        
        Args:
            sources: Fuentes a consultar
            limit: Número máximo de trends
            
        Returns:
            Lista de trends
        """
        logger.info(f"📡 Obteniendo trends (niche: {self.niche or 'general'})")
        
        trends = await self.trends_analyzer.get_trends(
            sources=sources or ["news", "twitter", "youtube"],
            niche=self.niche,
            limit=limit
        )
        
        logger.info(f"✓ {len(trends)} trends obtenidos")
        
        # Mostrar resumen
        for i, trend in enumerate(trends[:5], 1):
            logger.info(f"   {i}. {trend.topic}")
            logger.info(f"      Score: {trend.viral_score} | Source: {trend.source}")
        
        # Guardar en archivo
        await self._save_trends(trends)
        
        return trends
    
    async def _save_trends(self, trends: List) -> str:
        """Guarda los trends en un archivo JSON."""
        
        import json
        from datetime import datetime
        
        data_dir = settings.DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / "trends.json"
        
        trends_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "niche": self.niche,
            "count": len(trends),
            "trends": [
                {
                    "id": t.id,
                    "topic": t.topic,
                    "source": t.source,
                    "viral_score": t.viral_score,
                    "engagement": t.engagement,
                    "timestamp": t.timestamp,
                    "category": t.category,
                    "keywords": t.keywords
                }
                for t in trends
            ]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(trends_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Trends guardados en: {output_file}")
        
        return str(output_file)
    
    async def get_trending_topics(self, limit: int = 10) -> List[str]:
        """Obtiene solo los topics trending (lista simple)."""
        
        return await self.trends_analyzer.get_trending_topics(limit=limit)
    
    async def filter_by_score(
        self,
        min_score: int = 70
    ) -> List[Dict]:
        """Filtra trends por score mínimo."""
        
        trends = await self.trends_analyzer.get_trends(
            niche=self.niche,
            limit=50
        )
        
        filtered = [t for t in trends if t.viral_score >= min_score]
        
        logger.info(f"   {len(filtered)} trends con score >= {min_score}")
        
        return filtered