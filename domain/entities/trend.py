from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from domain.value_objects.viral_score import ViralScore
from domain.exceptions.trends import TrendNotFoundError


@dataclass
class TrendSource:
    """Fuente de una tendencia."""
    name: str
    type: str  # news, twitter, youtube, reddit


@dataclass
class Trend:
    """
    Entidad: una tendencia o tema trending.
    Tiene identidad (id) y puede mutar su estado.
    """
    id: str
    topic: str
    source: TrendSource
    viral_score: ViralScore
    engagement: int = 0
    category: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if not self.topic:
            raise TrendNotFoundError("El topic de la tendencia no puede estar vacío")

    def is_relevant_for(self, niche: str) -> bool:
        """Verifica si esta tendencia es relevante para un nicho."""
        niche_lower = niche.lower()
        return (
            (self.category and niche_lower in self.category.lower())
            or niche_lower in self.topic.lower()
            or any(niche_lower in kw.lower() for kw in self.keywords)
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "source": self.source.name,
            "source_type": self.source.type,
            "viral_score": int(self.viral_score),
            "engagement": self.engagement,
            "category": self.category,
            "keywords": self.keywords,
            "timestamp": self.timestamp,
        }
