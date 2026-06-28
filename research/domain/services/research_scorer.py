"""
ResearchScorer — Servicio de dominio para calcular puntajes
=============================================================
Calcula el ResearchScore de un topic basado en heurísticas simples.

REGRAS DE NEGOCIO:
  1. Relevance: basado en longitud del contenido y presencia de keywords
  2. Popularity: basado en la fuente (manual > google-news > twitter)
  3. Recency: basado en la fecha de publicación (más reciente = mejor)
  4. Source Reliability: proviene del ResearchSource.reliability

Puntos de extensión (futuro con IA):
  - ScorerExtension: inyectar un scorer de IA que SOBRESCRIBA
    los valores calculados por heurística
  - Se inyecta en el constructor, no se modifica esta clase

Uso:
    scorer = ResearchScorer()
    score = scorer.calculate(topic)

    # Con IA:
    scorer = ResearchScorer(ai_scorer=MyAIScorer())
    score = scorer.calculate(topic)  # IA puede sobreescribir valores
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from research.domain.value_objects.research_score import ResearchScore
from research.domain.entities.research_topic import ResearchTopic
from research.domain.ports.research_extensions import ScorerExtension


class ResearchScorer:
    """
    Servicio de dominio: calcula el puntaje de un ResearchTopic.

    Puramente funcional: calcula score basado en reglas de negocio.
    No tiene efectos secundarios ni conoce infraestructura.
    """

    # Keywords que suman relevance (configurable)
    _HIGH_VALUE_KEYWORDS: frozenset = frozenset({
        "inteligencia artificial", "ia", "ai", "openai", "chatgpt",
        "nuevo", "nueva", "descubrimiento", "revolucionario",
        "récord", "record", "histórico", "historico",
        "cambio", "futuro", "trending", "viral",
        "exclusivo", "primera vez", "nunca antes",
    })

    def __init__(self, ai_scorer: Optional[ScorerExtension] = None):
        """
        Args:
            ai_scorer: Extensión de IA para scoring (opcional, futuro)
        """
        self._ai_scorer = ai_scorer

    def calculate(self, topic: ResearchTopic) -> ResearchScore:
        """
        Calcula el score completo del topic.

        Si hay un AI Scorer configurado, se usa para complementar
        o sobreescribir los valores heurísticos.

        Args:
            topic: Topic a evaluar

        Returns:
            ResearchScore con todos los componentes calculados
        """
        relevance = self._calculate_relevance(topic)
        popularity = self._calculate_popularity(topic)
        recency = self._calculate_recency(topic)
        source_reliability = topic.source.reliability

        score = ResearchScore(
            relevance=relevance,
            popularity=popularity,
            recency=recency,
            source_reliability=source_reliability,
        )

        # Si hay IA, permite que sobreescriba el score
        if self._ai_scorer is not None:
            try:
                ai_score = self._ai_scorer.score(topic)
                score = self._merge_with_ai_score(score, ai_score)
            except Exception:
                # Si la IA falla, usar score heurístico (graceful degradation)
                pass

        return score

    # ── Heurísticas ──────────────────────────────────

    def _calculate_relevance(self, topic: ResearchTopic) -> int:
        """
        Calcula relevancia basada en:
          - Presencia de keywords de alto valor en título
          - Longitud del contenido (más contenido = más relevante)
          - Tiene descripción
        """
        score = 50  # Punto de partida neutral

        # Keywords en título
        title_lower = topic.title.lower()
        for kw in self._HIGH_VALUE_KEYWORDS:
            if kw in title_lower:
                score += 10
                break  # Solo una vez por keyword match

        # Contenido completo
        if len(topic.content) > 500:
            score += 15
        elif len(topic.content) > 200:
            score += 10
        elif len(topic.content) > 50:
            score += 5

        # Tiene descripción
        if len(topic.description) > 50:
            score += 10
        elif topic.description:
            score += 5

        # Tiene URL (es más verificable)
        if topic.url:
            score += 5

        # Tiene autor
        if topic.author:
            score += 5

        return min(100, max(0, score))

    def _calculate_popularity(self, topic: ResearchTopic) -> int:
        """
        Calcula popularidad basada en la fuente.
        Las fuentes manuales tienen más popularidad porque el usuario
        eligió ese tema específicamente.
        """
        base = {
            "manual": 80,
            "google-news": 60,
            "twitter": 40,
        }
        return base.get(topic.source.name, 50)

    def _calculate_recency(self, topic: ResearchTopic) -> int:
        """
        Calcula qué tan reciente es la noticia.
        - < 1 hora: 100
        - < 6 horas: 90
        - < 24 horas: 75
        - < 48 horas: 50
        - < 1 semana: 25
        - > 1 semana: 10
        - Sin fecha: 50 (neutral)
        """
        if topic.published_at is None:
            now = datetime.now(timezone.utc)
            if topic.created_at:
                # Usar created_at como aproximación
                delta = now - topic.created_at
            else:
                return 50
        else:
            delta = datetime.now(timezone.utc) - topic.published_at

        if delta < timedelta(hours=1):
            return 100
        elif delta < timedelta(hours=6):
            return 90
        elif delta < timedelta(hours=24):
            return 75
        elif delta < timedelta(hours=48):
            return 50
        elif delta < timedelta(days=7):
            return 25
        else:
            return 10

    # ── AI Score Merging ──────────────────────────────

    def _merge_with_ai_score(
        self,
        heuristic: ResearchScore,
        ai: ResearchScore,
    ) -> ResearchScore:
        """
        Combina el score heurístico con el de IA.

        Por ahora, la IA SOBRESCRIBE completamente el score.
        En el futuro se podría hacer un weighted average.
        """
        return ai

    def calculate_many(
        self, topics: list[ResearchTopic]
    ) -> list[ResearchTopic]:
        """
        Calcula score para múltiples topics in-place.

        Args:
            topics: Lista de topics (se modifican in-place)

        Returns:
            La misma lista con scores actualizados
        """
        for topic in topics:
            topic.score = self.calculate(topic)
        return topics
