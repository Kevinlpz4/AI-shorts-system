import logging
from datetime import datetime
from typing import Optional

from domain.entities.trend import Trend, TrendSource
from domain.value_objects.viral_score import ViralScore

logger = logging.getLogger(__name__)


class MockTrendSource:
    """
    Fuente de tendencias Mock para desarrollo/testing.
    
    Puerto que implementa: TrendSourcePort
    
    Genera tendencias ficticias de calidad para desarrollo.
    """
    
    def __init__(self, source_type: str = "news"):
        self._type = source_type
        self._name = f"mock-{source_type}"

        self._topics = {
            "tecnología": [
                "AI revoluciona la industria médica",
                "Nuevo chip cuántico de Google sorprende al mundo",
                "El futuro de los vehículos autónomos en 2025",
                "Criptomonedas y blockchain: la nueva era financiera",
                "Robots humanoides ya trabajan en fábricas",
            ],
            "negocios": [
                "Emprendedores que pasaron de cero a millones",
                "Startups que están cambiando la economía global",
                "Estrategias de marketing viral que funcionan",
                "Trabajo remoto: la tendencia que llegó para quedarse",
                "La economía del creador de contenido",
            ],
            "salud": [
                "Ejercicios de 5 minutos que transforman tu cuerpo",
                "Alimentos que dañan tu salud sin que lo sepas",
                "Nuevo descubrimiento médico revolucionario",
                "Bienestar mental: hábitos que cambian tu vida",
                "La ciencia del sueño y la productividad",
            ],
        }

        self._default_topics = [
            "IA generativa: el futuro ya está acá",
            "Tecnología que va a cambiar tu vida en 2025",
            "El secreto mejor guardado de Silicon Valley",
            "Por qué todos están hablando de esta nueva app",
            "Lo que nadie te dice sobre trabajar con IA",
        ]

    @property
    def source_name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return True

    async def fetch_trends(
        self,
        niche: Optional[str] = None,
        limit: int = 20,
    ) -> list[Trend]:
        """Genera trends mock."""
        topics = self._topics.get(niche, self._default_topics)
        trends = []

        source = TrendSource(name=self._name, type=self._type)

        for i, topic in enumerate(topics):
            trends.append(Trend(
                id=f"{self._type}_{i}_{datetime.utcnow().strftime('%Y%m%d')}",
                topic=topic,
                source=source,
                viral_score=ViralScore(85 - (i * 8)),
                engagement=10000 - (i * 1500),
                category=niche,
                keywords=[niche] if niche else [],
                timestamp=datetime.utcnow().isoformat(),
            ))

        return trends[:limit]
