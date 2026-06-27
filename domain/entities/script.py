from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from domain.value_objects.duration import Duration


@dataclass
class Script:
    """
    Entidad: un guion para short.
    
    Contiene hook, body, cta + metadatos.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    idea_id: str = ""
    topic: str = ""
    hook: str = ""
    body: str = ""
    cta: str = ""
    duration: Duration = field(default_factory=lambda: Duration(45))
    tone: str = "educational"
    format: str = "story"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def full_text(self) -> str:
        return f"{self.hook}. {self.body} {self.cta}"

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())

    def is_valid(self) -> bool:
        return (
            len(self.hook) >= 10
            and len(self.body) >= 50
            and len(self.cta) >= 5
        )

    def estimate_retention(self) -> float:
        """Estima retención basada en estructura del guion."""
        score = 50.0
        # Hook corto = mejor retención
        if len(self.hook.split()) <= 10:
            score += 15
        # Body con oraciones cortas
        sentences = self.body.split(".")
        avg_words = sum(len(s.split()) for s in sentences if s) / max(len([s for s in sentences if s]), 1)
        if avg_words < 12:
            score += 15
        # CTA con urgencia
        if any(w in self.cta.lower() for w in ["ahora", "ya", "sígueme"]):
            score += 10
        # Duración óptima
        if self.duration.is_optimal_for_shorts():
            score += 10
        return min(100, score)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "idea_id": self.idea_id,
            "topic": self.topic,
            "hook": self.hook,
            "body": self.body,
            "cta": self.cta,
            "duration": int(self.duration),
            "word_count": self.word_count,
            "tone": self.tone,
            "format": self.format,
        }
