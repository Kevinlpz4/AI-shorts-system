"""
ResearchScore — Puntaje de un ResearchTopic
=============================================
Value Object inmutable que representa la calidad/potencial de un topic.

Componentes del score:
  - relevance (35%): qué tan relevante es para la audiencia
  - popularity (25%): qué tan popular/difundido es el tema
  - recency (25%): qué tan reciente es la noticia
  - source_reliability (15%): confiabilidad de la fuente

El peso de cada componente puede ajustarse en el futuro sin modificar
el value object (se configura en el servicio de scoring).

La propiedad 'total' calcula el weighted average.

Puntos de extensión para IA:
  - En el futuro, un ScorerExtension puede calcular relevance/popularity
    usando un modelo de ML en lugar de heurísticas simples.
  - Se inyecta en ResearchScorer (servicio de dominio), no acá.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchScore:
    """
    Value Object: puntaje de un topic de investigación.

    Inmutable y autovalidante.
    Implementa __lt__ para ordenar topics por score.
    """

    relevance: int = 0       # 0-100
    popularity: int = 0      # 0-100
    recency: int = 0         # 0-100
    source_reliability: int = 0  # 0-100

    # Pesos para el cálculo del score total
    _RELEVANCE_WEIGHT: float = 0.35
    _POPULARITY_WEIGHT: float = 0.25
    _RECENCY_WEIGHT: float = 0.25
    _RELIABILITY_WEIGHT: float = 0.15

    def __post_init__(self):
        for field_name in ("relevance", "popularity", "recency", "source_reliability"):
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise TypeError(f"{field_name} debe ser int, no {type(value).__name__}")
            if not 0 <= value <= 100:
                raise ValueError(
                    f"{field_name} debe estar entre 0-100, no {value}"
                )

    @property
    def total(self) -> float:
        """
        Score total ponderado (0-100).

        Fórmula:
          total = relevance*0.35 + popularity*0.25 + recency*0.25 + reliability*0.15

        Punto de extensión: cuando se integre IA, un ScorerExtension
        puede recalcular los componentes individuales. El total siempre
        se calcula con esta fórmula (es regla de negocio).
        """
        return round(
            self.relevance * self._RELEVANCE_WEIGHT
            + self.popularity * self._POPULARITY_WEIGHT
            + self.recency * self._RECENCY_WEIGHT
            + self.source_reliability * self._RELIABILITY_WEIGHT,
            1,
        )

    @property
    def is_notable(self) -> bool:
        """Un score es notable si supera 70 puntos."""
        return self.total >= 70

    def __lt__(self, other: "ResearchScore") -> bool:
        """Para ordenar: mejor score primero (orden descendente)."""
        return self.total > other.total  # invertido: mejor score primero

    def __str__(self) -> str:
        return f"ResearchScore({self.total:.1f}: R{self.relevance}/P{self.popularity}/Rec{self.recency}/S{self.source_reliability})"
