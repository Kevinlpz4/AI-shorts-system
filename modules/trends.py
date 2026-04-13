"""
Trends Analyzer - Obtención de Tendencias
==========================================
Módulo para analizar y obtener tendencias actuales.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from app.config import settings
from app.logger import logger
from services.news_service import NewsService
from services.social_service import SocialService


@dataclass
class Trend:
    """Representa una tendencia."""
    id: str
    topic: str
    source: str
    viral_score: int
    engagement: int
    timestamp: str
    category: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class TrendsAnalyzer:
    """
    Analizador de tendencias para contenido viral.
    
    Obtiene trends de múltiples fuentes:
    - News API (noticias)
    - Redes sociales (Twitter/X, Reddit)
    - YouTube trending
    """
    
    def __init__(self):
        self.news_service = NewsService()
        self.social_service = SocialService()
        
    async def get_trends(
        self,
        sources: List[str] = None,
        niche: Optional[str] = None,
        limit: int = 20
    ) -> List[Trend]:
        """
        Obtiene tendencias de las fuentes especificadas.
        
        Args:
            sources: Fuentes a consultar ["news", "twitter", "youtube", "reddit"]
            niche: Nicho específico (tecnología, negocios, etc.)
            limit: Número máximo de trends
            
        Returns:
            Lista de tendencias ordenadas por potencial viral
        """
        sources = sources or ["news", "twitter", "youtube"]
        logger.info(f"📡 Obteniendo trends de: {sources} (nicho: {niche})")
        
        all_trends = []
        
        # Obtener de cada fuente
        for source in sources:
            trends = await self._fetch_from_source(source, niche)
            all_trends.extend(trends)
        
        # Ordenar por viral_score y limitar
        all_trends.sort(key=lambda x: x.viral_score, reverse=True)
        
        return all_trends[:limit]
    
    async def _fetch_from_source(
        self,
        source: str,
        niche: Optional[str]
    ) -> List[Trend]:
        """Obtiene trends de una fuente específica."""
        
        if source == "news":
            return await self._fetch_news(niche)
        elif source == "twitter":
            return await self._fetch_twitter(niche)
        elif source == "youtube":
            return await self._fetch_youtube(niche)
        elif source == "reddit":
            return await self._fetch_reddit(niche)
        
        return []
    
    async def _fetch_news(self, niche: Optional[str]) -> List[Trend]:
        """Obtiene tendencias de News API."""
        try:
            articles = await self.news_service.get_top_headlines(
                category=niche,
                country="us"
            )
            
            trends = []
            for i, article in enumerate(articles):
                trends.append(Trend(
                    id=f"news_{i}",
                    topic=article.get("title", ""),
                    source="news",
                    viral_score=self._calculate_viral_score(
                        article.get("popularity", 0),
                        article.get("engagement", 0)
                    ),
                    engagement=article.get("engagement", 0),
                    timestamp=datetime.utcnow().isoformat(),
                    category=niche,
                    keywords=self._extract_keywords(article.get("title", ""))
                ))
            
            return trends
            
        except Exception as e:
            logger.warning(f"Error fetching news: {e}")
            return self._get_mock_trends("news", niche)
    
    async def _fetch_twitter(self, niche: Optional[str]) -> List[Trend]:
        """Obtiene tendencias de Twitter/X."""
        # TODO: Conectar con Twitter API
        return self._get_mock_trends("twitter", niche)
    
    async def _fetch_youtube(self, niche: Optional[str]) -> List[Trend]:
        """Obtiene tendencias de YouTube."""
        # TODO: Conectar con YouTube API
        return self._get_mock_trends("youtube", niche)
    
    async def _fetch_reddit(self, niche: Optional[str]) -> List[Trend]:
        """Obtiene tendencias de Reddit."""
        # TODO: Conectar con Reddit API
        return self._get_mock_trends("reddit", niche)
    
    def _calculate_viral_score(self, popularity: int, engagement: int) -> int:
        """Calcula el score viral (0-100)."""
        # Fórmula simple: combinación de popularidad y engagement
        score = min(100, (popularity * 0.3) + (engagement * 0.7 / 100))
        return int(score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae keywords de un texto."""
        # Implementación básica
        words = text.lower().split()
        # Palabras comunes a excluir
        stopwords = {"the", "a", "an", "is", "are", "was", "of", "in", "on", "at"}
        return [w for w in words if len(w) > 3 and w not in stopwords][:5]
    
    def _get_mock_trends(self, source: str, niche: Optional[str]) -> List[Trend]:
        """Retorna trends mock para desarrollo."""
        topics = {
            "tecnología": [
                "AI revoluciona la industria médica",
                "Nuevo chip cuántico de Google",
                "El futuro de los vehículos autónomos",
                "Criptomonedas y blockchain 2025",
                "Robots en el hogar"
            ],
            "negocios": [
                "Emprendedores exitosos",
                "Startups que cuestan millones",
                "Estrategias de marketing viral",
                "Trabajo remoto tendencias",
                "Economía mundial actual"
            ],
            "salud": [
                "Ejercicios para estar en forma",
                "Alimentos que dañan tu salud",
                "Nuevo descubrimiento médico",
                "Bienestar mental tips",
                "Sueño y productividad"
            ]
        }
        
        default_topics = topics.get(niche, [
            f"Noticia trending {i}" for i in range(1, 6)
        ])
        
        trends = []
        for i, topic in enumerate(default_topics):
            trends.append(Trend(
                id=f"{source}_{i}",
                topic=topic,
                source=source,
                viral_score=85 - (i * 5),
                engagement=10000 - (i * 1500),
                timestamp=datetime.utcnow().isoformat(),
                category=niche
            ))
        
        return trends
    
    async def filter_by_niche(
        self,
        trends: List[Trend],
        niche: str
    ) -> List[Trend]:
        """Filtra trends por nicho específico."""
        return [t for t in trends if t.category == niche or niche in t.topic.lower()]
    
    async def get_trending_topics(self, limit: int = 10) -> List[str]:
        """Retorna lista de topics trending (para uso rápido)."""
        trends = await self.get_trends(limit=limit)
        return [t.topic for t in trends]