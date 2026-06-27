from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from domain.value_objects.viral_score import ViralScore
from domain.value_objects.hook_type import HookType


@dataclass
class ContentIdea:
    """
    Entidad: una idea de contenido.
    
    Es el AGGREGATE ROOT de la generación de contenido.
    Una idea contiene su hook, formato, y metadata.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    hook: str = ""
    topic: str = ""
    description: str = ""
    target_audience: str = "general"
    format: str = "story"
    viral_score: ViralScore = field(default_factory=lambda: ViralScore(50))
    keywords: list[str] = field(default_factory=list)
    trend_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def is_viable(self) -> bool:
        """Una idea es viable si tiene hook y score aceptable."""
        return len(self.hook) >= 5 and self.viral_score.is_promising()

    def evaluate_hook_quality(self) -> int:
        """Evalúa calidad del hook (0-100)."""
        score = 50
        if "?" in self.hook:
            score += 15
        if any(w in self.hook.lower() for w in ["secreto", "verdad", "nadie", "increíble"]):
            score += 10
        if len(self.hook.split()) <= 15:
            score += 15
        if any(c.isdigit() for c in self.hook):
            score += 10
        return min(100, score)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hook": self.hook,
            "topic": self.topic,
            "format": self.format,
            "viral_score": int(self.viral_score),
            "description": self.description,
            "audience": self.target_audience,
            "keywords": self.keywords,
            "trend_id": self.trend_id,
            "created_at": self.created_at,
        }
