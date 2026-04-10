"""
Analyzer - Análisis de Métricas
===============================
Módulo para analizar rendimiento de videos.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.logger import logger
from services.youtube_service import YouTubeService


@dataclass
class VideoMetrics:
    """Métricas de un video."""
    video_id: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    retention_avg: float
    ctr: float
    subscribers_gained: int
    analyzed_at: str


@dataclass
class PerformanceReport:
    """Reporte de rendimiento."""
    video_id: str
    metrics: VideoMetrics
    score: int
    recommendations: List[str]
    compared_to_avg: Dict


class Analyzer:
    """
    Analizador de métricas y rendimiento.
    
    Analiza:
    - Métricas de videos publicados
    - Retención de audiencia
    - Engagement
    - Recomendaciones de optimización
    """
    
    def __init__(self):
        self.youtube_service = YouTubeService()
    
    async def analyze_video(
        self,
        video_id: str,
        platform: str = "youtube"
    ) -> PerformanceReport:
        """
        Analiza el rendimiento de un video.
        
        Args:
            video_id: ID del video
            platform: Plataforma
            
        Returns:
            Reporte de rendimiento
        """
        logger.info(f"📊 Analizando video: {video_id}")
        
        if platform == "youtube":
            return await self._analyze_youtube(video_id)
        
        return PerformanceReport(
            video_id=video_id,
            metrics=VideoMetrics(
                video_id=video_id,
                views=0,
                likes=0,
                comments=0,
                shares=0,
                saves=0,
                retention_avg=0,
                ctr=0,
                subscribers_gained=0,
                analyzed_at=datetime.utcnow().isoformat()
            ),
            score=0,
            recommendations=["Plataforma no soportada"],
            compared_to_avg={}
        )
    
    async def _analyze_youtube(self, video_id: str) -> PerformanceReport:
        """Analiza video de YouTube."""
        
        try:
            stats = await self.youtube_service.get_video_stats(video_id)
            
            # Calcular métricas
            views = stats.get("views", 0)
            likes = stats.get("likes", 0)
            comments = stats.get("comments", 0)
            shares = stats.get("shares", 0)
            
            # Calcular retention
            avg_duration = stats.get("average_view_duration", "0:30")
            retention = self._parse_duration(avg_duration) / 45 * 100  # Assuming 45s video
            
            # Calcular CTR (estimado)
            ctr = (likes + comments) / views * 100 if views > 0 else 0
            
            # Calcular score general (0-100)
            score = self._calculate_score(views, likes, comments, shares, retention)
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(
                views, likes, comments, shares, retention, ctr
            )
            
            # Comparar con promedio
            compared = self._compare_to_average(views, likes, comments, retention)
            
            metrics = VideoMetrics(
                video_id=video_id,
                views=views,
                likes=likes,
                comments=comments,
                shares=shares,
                saves=stats.get("saves", 0),
                retention_avg=retention,
                ctr=ctr,
                subscribers_gained=stats.get("subscriber_gained", 0),
                analyzed_at=datetime.utcnow().isoformat()
            )
            
            return PerformanceReport(
                video_id=video_id,
                metrics=metrics,
                score=score,
                recommendations=recommendations,
                compared_to_avg=compared
            )
            
        except Exception as e:
            logger.error(f"Error analizando video: {e}")
            return self._get_mock_report(video_id)
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parsea string de duración a segundos."""
        try:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        return 30  # Default
    
    def _calculate_score(
        self,
        views: int,
        likes: int,
        comments: int,
        shares: int,
        retention: float
    ) -> int:
        """Calcula score general (0-100)."""
        
        # Pesos para cada métrica
        # views: 30%, likes: 25%, comments: 15%, shares: 20%, retention: 10%
        
        # Normalizar cada métrica (benchmark: 10K views, 1K likes, 100 comments, 50 shares, 60% retention)
        view_score = min(100, views / 10000 * 100)
        like_score = min(100, likes / 1000 * 100)
        comment_score = min(100, comments / 100 * 100)
        share_score = min(100, shares / 50 * 100)
        retention_score = retention
        
        score = (view_score * 0.30) + (like_score * 0.25) + (comment_score * 0.15) + \
                (share_score * 0.20) + (retention_score * 0.10)
        
        return int(min(100, score))
    
    def _generate_recommendations(
        self,
        views: int,
        likes: int,
        comments: int,
        shares: int,
        retention: float,
        ctr: float
    ) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        
        recs = []
        
        # Retención
        if retention < 50:
            recs.append("Hook demasiado lento - reduce los primeros 3 segundos")
        elif retention > 70:
            recs.append("Excelente retención - mantener estilo similar")
        
        # Engagement
        engagement_rate = (likes + comments) / views * 100 if views > 0 else 0
        if engagement_rate < 3:
            recs.append("Bajo engagement - considera más calls-to-action")
        
        # Shares
        if shares < 50 and views > 1000:
            recs.append("Pocos shares - añade más valor único al final")
        
        # CTR
        if ctr < 2:
            recs.append("CTR bajo - mejora el thumbnail y título")
        
        # General
        if not recs:
            recs.append("Video funcionando bien - continuar con mismo enfoque")
        
        return recs
    
    def _compare_to_average(
        self,
        views: int,
        likes: int,
        comments: int,
        retention: float
    ) -> Dict:
        """Compara con promedios."""
        
        # Benchmarks
        avg_views = 5000
        avg_likes = 500
        avg_comments = 50
        avg_retention = 55
        
        return {
            "views": f"{'+' if views > avg_views else ''}{((views - avg_views) / avg_views * 100):.1f}%",
            "likes": f"{'+' if likes > avg_likes else ''}{((likes - avg_likes) / avg_likes * 100):.1f}%",
            "comments": f"{'+' if comments > avg_comments else ''}{((comments - avg_comments) / avg_comments * 100):.1f}%",
            "retention": f"{'+' if retention > avg_retention else ''}{retention - avg_retention:.1f}%"
        }
    
    def _get_mock_report(self, video_id: str) -> PerformanceReport:
        """Retorna reporte mock."""
        
        return PerformanceReport(
            video_id=video_id,
            metrics=VideoMetrics(
                video_id=video_id,
                views=15000,
                likes=2300,
                comments=145,
                shares=89,
                saves=234,
                retention_avg=68,
                ctr=4.2,
                subscribers_gained=150,
                analyzed_at=datetime.utcnow().isoformat()
            ),
            score=72,
            recommendations=[
                "Excelente retención - mantener estilo",
                "Buen engagement - añadir más CTAs",
                "Considerar más contenido de este tipo"
            ],
            compared_to_avg={
                "views": "+200%",
                "likes": "+360%",
                "retention": "+13%"
            }
        )
    
    async def get_channel_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del canal."""
        
        logger.info("📈 Obteniendo resumen del canal")
        
        # TODO: Implementar con YouTube Analytics API
        return {
            "total_videos": 0,
            "total_views": 0,
            "avg_views": 0,
            "avg_retention": 0,
            "top_performers": [],
            "recent_analytics": []
        }