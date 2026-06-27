from dataclasses import dataclass, field
from typing import Optional

from domain.value_objects.hook_type import HookType


@dataclass
class Hook:
    """
    Entidad: un hook viral.
    
    Un hook es la primera impresión del video.
    Determina si el usuario sigue viendo o hace scroll.
    """
    id: str = ""
    text: str = ""
    hook_type: HookType = HookType.STATEMENT
    score: int = 50
    variations: list[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.hook_type, str):
            self.hook_type = HookType.from_string(self.hook_type)

    @property
    def is_strong(self) -> bool:
        return self.score >= 75

    @property
    def length_quality(self) -> str:
        word_count = len(self.text.split())
        if word_count <= 8:
            return "excelente"
        elif word_count <= 12:
            return "bueno"
        elif word_count <= 15:
            return "aceptable"
        return "largo"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.hook_type.value,
            "score": self.score,
            "length_quality": self.length_quality,
            "variations": self.variations,
        }
