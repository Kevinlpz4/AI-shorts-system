"""
Research Extension Points — Puertos para extensiones futuras de IA
====================================================================
Estos puertos NO se implementan ahora.
Son puntos de extensión para cuando se integre IA en el módulo Research.

Cada uno define un contrato que una implementación de IA (o cualquier
otra estrategia) debe cumplir.

Regla: todas estas extensiones se inyectan en los servicios de dominio
o casos de uso. Nunca se modifican clases existentes al agregar una nueva.

Cómo agregar una extensión (OCP ✅):
  1. Definir el Protocol acá
  2. Crear implementación en infrastructure/
  3. Inyectar en el servicio de dominio correspondiente
  4. Nunca modificar domain/ existente
"""

from typing import Optional, Protocol

from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_score import ResearchScore


class ScorerExtension(Protocol):
    """
    FUTURO: Extensión para puntuar noticias usando IA.

    Reemplaza o complementa las heurísticas básicas de ResearchScorer.

    Ejemplo de implementación:
      class AIScorer:
          async def score(self, topic: ResearchTopic) -> ResearchScore:
              prompt = f"Puntuá esta noticia del 1 al 100..."
              result = await ai.generate(prompt)
              return ResearchScore(relevance=result.relevance, ...)
    """

    async def score(self, topic: ResearchTopic) -> ResearchScore:
        """
        Calcula un score para el topic usando IA.

        Returns:
            ResearchScore con los componentes calculados por IA
        """
        ...


class SummarizerExtension(Protocol):
    """
    FUTURO: Extensión para resumir noticias usando IA.

    Genera un resumen conciso del contenido para mostrarlo al usuario
    en la interfaz de aprobación.
    """

    async def summarize(self, content: str, max_length: int = 200) -> str:
        """
        Resumen del contenido.

        Args:
            content: Contenido completo a resumir
            max_length: Longitud máxima del resumen

        Returns:
            Texto resumido
        """
        ...


class CategoryClassifier(Protocol):
    """
    FUTURO: Extensión para clasificar categorías automáticamente.

    Ej: "tecnología", "ciencia", "entretenimiento", etc.
    """

    async def classify(self, topic: ResearchTopic) -> list[str]:
        """
        Clasifica el topic en categorías.

        Returns:
            Lista de categorías
        """
        ...


class ViralDetector(Protocol):
    """
    FUTURO: Extensión para detectar potencial viral.

    Evalúa si una noticia tiene potencial para volverse viral
    basado en su contenido, tendencias actuales, etc.
    """

    async def detect_viral_potential(self, topic: ResearchTopic) -> float:
        """
        Detecta potencial viral.

        Returns:
            Score de 0.0 a 1.0 indicando potencial viral
        """
        ...


class FakeNewsDetector(Protocol):
    """
    FUTURO: Extensión para detectar fake news.

    Evalúa la veracidad de la información antes de permitir
    que sea aprobada para generación de contenido.
    """

    async def verify(self, topic: ResearchTopic) -> tuple[bool, float, str]:
        """
        Verifica la veracidad del contenido.

        Returns:
            Tuple (es_confiable, confianza_0-1, explicación)
        """
        ...
