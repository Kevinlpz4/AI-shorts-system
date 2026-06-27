import json
import logging
from typing import Optional

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration

logger = logging.getLogger(__name__)


class MockAIProvider:
    """
    Proveedor de IA Mock para desarrollo/testing.
    
    Puerto que implementa: AIProvider, IdeaGeneratorPort, ScriptGeneratorPort
    Útil cuando no hay APIs disponibles o para tests.
    """
    
    def __init__(self):
        self._name = "mock"

    @property
    def name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return True

    async def generate(self, prompt: str, **kwargs) -> str:
        """Genera texto mock."""
        prompt_lower = prompt.lower()

        if "guion" in prompt_lower or "script" in prompt_lower:
            return self._get_mock_script()
        if "idea" in prompt_lower:
            return json.dumps({
                "hook": "Esta IA ya está reemplazando trabajos",
                "format": "story",
                "description": "Contenido sobre IA y el futuro del trabajo",
                "audience": "general",
            })
        return "Contenido generado con fallback — las APIs de IA no tienen créditos disponibles."

    async def generate_json(self, prompt: str, **kwargs) -> dict:
        """Genera JSON mock."""
        response = await self.generate(prompt, **kwargs)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {}

    async def generate_ideas(
        self,
        trends: list,
        niche: Optional[str] = None,
        count: int = 5,
    ) -> list[ContentIdea]:
        """Genera ideas mock."""
        ideas = []
        templates = [
            "5 cosas sobre {topic} que debés saber",
            "¿Sabías esto sobre {topic}?",
            "El secreto de {topic} que nadie te cuenta",
            "Por esto {topic} es trending ahora",
            "{topic} va a cambiar todo en 2025",
        ]

        for i in range(count):
            topic = trends[i % len(trends)].topic if trends else (niche or "tecnología")
            hook = templates[i % len(templates)].format(topic=topic)

            ideas.append(ContentIdea(
                hook=hook,
                topic=topic,
                format=["story", "list", "fact", "tutorial", "reaction"][i % 5],
                description=f"Idea basada en {topic}",
                target_audience="general",
                viral_score=ViralScore(80 - i * 10),
                trend_id=trends[i % len(trends)].id if trends else None,
                keywords=[topic],
            ))

        return ideas

    async def generate_script(
        self,
        idea: ContentIdea,
        duration: int = 45,
        tone: str = "educational",
    ) -> Script:
        """Genera script mock."""
        return Script(
            idea_id=idea.id,
            topic=idea.topic,
            hook=idea.hook,
            body=(
                f"Acá te cuento los detalles sobre {idea.topic}. "
                f"Esto es lo que nadie te dice y necesitás saber. "
                f"Prestá atención porque esto puede cambiar tu perspectiva. "
                f"La inteligencia artificial ya está cambiando el mundo del trabajo, "
                f"y lo más impactante es que probablemente ya la usaste."
            ),
            cta="Seguime para más contenido 🔥",
            duration=Duration(duration),
            tone=tone,
            format=idea.format,
        )

    def _get_mock_script(self) -> str:
        """Retorna script mock de calidad."""
        return json.dumps({
            "hook": "Esta inteligencia artificial ya está reemplazando trabajos",
            "body": (
                "Esta inteligencia artificial ya está cambiando el mundo del trabajo, "
                "y lo más impactante es que probablemente ya la has usado. "
                "Se llama ChatGPT, y puede hacer tareas que antes tomaban horas en solo minutos. "
                "Desde escribir textos, responder clientes, hasta programar código básico. "
                "Empresas de todo el mundo ya la están usando para automatizar procesos. "
                "Pero acá viene lo fuerte: no necesitás ser experto para usarla. "
                "Hoy, cualquier persona puede hacer el trabajo de varios "
                "con solo saber cómo usar esta herramienta."
            ),
            "cta": "Seguime para más contenido de tecnología que va a cambiar tu vida 🔥",
        })
