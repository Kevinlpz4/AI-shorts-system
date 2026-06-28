"""
MockResearchSource — Fuente de investigación simulada
=======================================================
Implementa ResearchSourcePort con datos ficticios.

Propósito:
  1. Testing: permite testear casos de uso sin APIs reales
  2. Development: el módulo funciona completo sin conexión
  3. Demo: mostrar el sistema funcionando sin configurar APIs

NO se usa en producción (obviamente).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from research.domain.ports.research_source import ResearchSourcePort, RawResearchData


# ── Datos simulados ──────────────────────────────────

_MOCK_TOPICS: list[dict] = [
    {
        "title": "Nuevo modelo de IA supera a GPT-4 en razonamiento lógico",
        "description": "Un equipo de investigadores presentó un nuevo modelo que alcanza un 95% de precisión en pruebas de razonamiento.",
        "content": (
            "Un equipo internacional de investigadores ha desarrollado un nuevo modelo de inteligencia artificial "
            "que supera significativamente a GPT-4 en tareas de razonamiento lógico. El modelo, llamado LogicNet, "
            "alcanzó un 95% de precisión en el benchmark ARC (Abstraction and Reasoning Corpus), superando el 87% "
            "de GPT-4. Los investigadores destacan que el modelo no solo memoriza patrones sino que realmente "
            "comprende las relaciones lógicas subyacentes. Este avance podría tener implicaciones significativas "
            "en campos como la programación automatizada, el análisis de datos y la investigación científica. "
            "El equipo planea publicar el paper y el código fuente en las próximas semanas."
        ),
        "url": "https://example.com/ai/logicnet-supera-gpt4",
        "author": "María García",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=2),
    },
    {
        "title": "YouTube lanza herramienta de doblaje automático con IA para creadores",
        "description": "La nueva función permite traducir y doblar videos automáticamente a más de 20 idiomas.",
        "content": (
            "YouTube anunció el lanzamiento de una nueva herramienta de doblaje automático impulsada por IA "
            "que permitirá a los creadores de contenido llegar a audiencias globales sin necesidad de grabar "
            "múltiples pistas de audio. La herramienta, actualmente en beta, soporta más de 20 idiomas y "
            "puede sincronizar el movimiento de labios con el audio traducido. Los creadores pueden revisar "
            "y editar las traducciones antes de publicar. YouTube planea expandir la herramienta a más "
            "idiomas y mejorar la calidad del doblaje en los próximos meses."
        ),
        "url": "https://example.com/tech/youtube-doblaje-ia",
        "author": "Carlos López",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=5),
    },
    {
        "title": "Estudio revela que los Shorts de menos de 30 segundos tienen 3x más engagement",
        "description": "Un análisis de más de 10 millones de videos muestra que la duración óptima para Shorts es de 15 a 30 segundos.",
        "content": (
            "Un estudio reciente analizó más de 10 millones de Shorts en YouTube y TikTok para determinar "
            "la duración óptima que maximiza el engagement. Los resultados muestran que los videos de entre "
            "15 y 30 segundos tienen 3 veces más interacciones que los videos más largos. El estudio también "
            "encontró que los primeros 3 segundos son críticos para retener la atención del espectador. "
            "Los investigadores recomiendan que los creadores se enfoquen en hooks fuertes al inicio y "
            "mantengan un ritmo rápido durante todo el video."
        ),
        "url": "https://example.com/research/shorts-duracion-optima",
        "author": None,
        "published_at": datetime.now(timezone.utc) - timedelta(days=1),
    },
    {
        "title": "Nueva técnica de edición de video con IA reduce tiempo de producción 80%",
        "description": "Una startup española desarrolló una herramienta que automatiza la post-producción de videos cortos.",
        "content": (
            "La startup española ClipAI ha lanzado una herramienta de edición de video impulsada por IA "
            "que promete reducir el tiempo de post-producción en un 80%. La herramienta analiza el contenido "
            "del video, identifica los momentos más relevantes, y automáticamente genera cortes, transiciones "
            "y subtítulos. Los creadores solo necesitan revisar y ajustar el resultado final. ClipAI ya ha "
            "asegurado una ronda de inversión de 2 millones de euros y planea lanzar una versión gratuita "
            "para creadores principiantes."
        ),
        "url": "https://example.com/tech/clipai-edicion-ia",
        "author": "Ana Martínez",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=12),
    },
    {
        "title": "El algoritmo de TikTok ahora prioriza contenido educativo sobre entretenimiento",
        "description": "TikTok actualiza su algoritmo para promover contenido educativo y formativo.",
        "content": (
            "TikTok ha anunciado una actualización significativa de su algoritmo de recomendación que ahora "
            "prioriza el contenido educativo y formativo sobre el puramente entretenido. La plataforma reportó "
            "que los videos educativos tienen un 40% más de retención y generan conversaciones más significativas. "
            "Creadores de contenido educativo han visto un aumento del 150% en sus vistas desde que se implementó "
            "el cambio. TikTok también planea lanzar un fondo de 10 millones de dólares para apoyar a creadores "
            "de contenido educativo."
        ),
        "url": "https://example.com/social/tiktok-algoritmo-educativo",
        "author": "Pedro Sánchez",
        "published_at": datetime.now(timezone.utc) - timedelta(hours=8),
    },
]


class MockResearchSource:
    """
    Fuente de investigación simulada.

    Implementa ResearchSourcePort usando datos mock.
    Útil para testing, desarrollo y demo.

    Uso:
        source = MockResearchSource()
        results = await source.fetch(query="IA", limit=3)
    """

    def __init__(self, name: str = "mock", available: bool = True):
        self._name = name
        self._available = available

    @property
    def source_name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return self._available

    async def fetch(
        self,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> list[RawResearchData]:
        """
        Retorna datos simulados.

        Si hay query, filtra los títulos que contengan el término.
        Si no hay query, retorna todos los topics disponibles.
        """
        if not self._available:
            from research.domain.exceptions import SourceNotAvailableError
            raise SourceNotAvailableError(source_name=self._name)

        results = list(_MOCK_TOPICS)

        # Filtrar por query si se especifica
        if query:
            query_lower = query.lower()
            results = [
                r for r in results
                if query_lower in r["title"].lower()
                or query_lower in r["description"].lower()
            ]

        # Limitar resultados
        results = results[:limit]

        return [
            RawResearchData(
                title=r["title"],
                description=r["description"],
                content=r["content"],
                url=r["url"],
                author=r["author"],
                published_at=r["published_at"],
            )
            for r in results
        ]

    def __repr__(self) -> str:
        return f"MockResearchSource(name='{self._name}', available={self._available})"
