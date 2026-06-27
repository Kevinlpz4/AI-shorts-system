from typing import Protocol, Optional, runtime_checkable

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.trend import Trend


@runtime_checkable
class AIProvider(Protocol):
    """
    Puerto: Proveedor de IA para generación de contenido.
    
    Cualquier implementación (OpenAI, Anthropic, Gemini, mock)
    debe cumplir con este contrato.
    """
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Genera texto a partir de un prompt."""
        ...

    async def generate_json(self, prompt: str, **kwargs) -> dict:
        """Genera respuesta estructurada en JSON."""
        ...

    @property
    def name(self) -> str:
        """Nombre del proveedor."""
        ...

    @property
    def available(self) -> bool:
        """Indica si el proveedor está disponible."""
        ...


class IdeaGeneratorPort(Protocol):
    """Puerto: Generador de ideas de contenido."""
    
    async def generate_ideas(
        self,
        trends: list[Trend],
        niche: Optional[str] = None,
        count: int = 5,
    ) -> list[ContentIdea]:
        ...


class ScriptGeneratorPort(Protocol):
    """Puerto: Generador de guiones."""
    
    async def generate_script(
        self,
        idea: ContentIdea,
        duration: int = 45,
        tone: str = "educational",
    ) -> Script:
        ...
