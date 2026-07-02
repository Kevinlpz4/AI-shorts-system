"""
AI Service - Servicio legacy de IA
====================================
Servicio unificado que usa OpenRouter como ÚNICO proveedor de IA.

CONCEPTO:
  - Internamente usa el SDK de OpenAI porque OpenRouter es API-compatible.
  - El DOMINIO no sabe esto — es un detalle de implementación.
  - Mantiene la misma interfaz pública para compatibilidad con módulos legacy.

Uso (legacy):
    ai = AIService()
    result = await ai.generate("prompt")
    idea = await ai.generate_idea(trends)
    script = await ai.generate_script("idea")

ATENCIÓN:
  Este servicio es LEGACY. El código nuevo debe usar:
    domain/ports/ai_provider.py → AIProvider Protocol
    infrastructure/ai/openrouter_provider.py → OpenRouterProvider
    + DI via Container
"""

from typing import Optional, Dict, List

# OpenRouter es compatible con la API de OpenAI,
# así que usamos el SDK de OpenAI como cliente HTTP.
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from app.config import settings
from app.logger import logger


class AIService:
    """
    Servicio unificado de IA vía OpenRouter.

    OpenRouter permite acceder a múltiples modelos (OpenAI, Anthropic,
    Google, Mistral, etc.) con UNA sola API key.

    La selección del PROVEEDOR desapareció — siempre OpenRouter.
    La selección del MODELO permanece configurable.
    """

    # Singleton para evitar múltiples inicializaciones
    _instance = None
    _initialized = False

    def __new__(cls, provider: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, provider: Optional[str] = None):
        """
        Inicializa el servicio.

        Args:
            provider: Ignorado (se mantiene por compatibilidad).
                      Siempre usa OpenRouter.
        """
        if not AIService._initialized:
            self.provider_name = "openrouter"
            self._init_clients()
            AIService._initialized = True

    def _init_clients(self):
        """Inicializa el cliente de OpenRouter (API compatible con OpenAI)."""
        self.client = None

        if OPENAI_AVAILABLE and settings.OPENROUTER_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )
            logger.info("✅ OpenRouter client inicializado (base: %s)", settings.OPENROUTER_BASE_URL)
        else:
            logger.warning("⚠️ OpenRouter no disponible: falta OPENROUTER_API_KEY")

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        provider: Optional[str] = None,
    ) -> str:
        """
        Genera texto usando OpenRouter.

        Args:
            prompt: Prompt para el modelo
            model: Modelo (ej: "anthropic/claude-sonnet-4"). Default: OPENROUTER_MODEL
            temperature: Temperatura de generación
            max_tokens: Máximo de tokens
            provider: Ignorado (se mantiene por compatibilidad)

        Returns:
            Texto generado
        """
        if not self.client:
            logger.warning("⚠️ OpenRouter no disponible, usando fallback")
            return await self._generate_fallback(prompt)

        try:
            model = model or settings.OPENROUTER_MODEL
            temperature = temperature or settings.OPENROUTER_TEMPERATURE
            max_tokens = max_tokens or settings.OPENROUTER_MAX_TOKENS

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Sos un experto en contenido viral para YouTube Shorts. Respondé siempre en español.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Error en OpenRouter: {e}")
            return await self._generate_fallback(prompt)

    async def generate_json(
        self,
        prompt: str,
        schema: Dict = None,
        **kwargs,
    ) -> Dict:
        """Genera respuesta en formato JSON."""
        json_prompt = prompt + "\n\nResponde en formato JSON válido."

        if schema:
            json_prompt += f"\n\nSchema requerido: {schema}"

        response = await self.generate(json_prompt, **kwargs)

        import json
        try:
            return json.loads(response)
        except:
            logger.warning("No se pudo parsear JSON")
            return {}

    async def generate_idea(self, trends: list) -> str:
        """Genera una idea viral basada en trends."""
        trends_text = "\n".join([f"- {t}" for t in trends])

        prompt = f"""Eres un experto en contenido viral para YouTube Shorts.

Basado en estas tendencias:
{trends_text}

Genera UNA idea viral con:
- Hook atractivo (máx 15 palabras)
- Formato (story/list/reaction/tutorial/fact)
- Descripción breve
- Audiencia objetivo

Responde en JSON:
{{
  "hook": "...",
  "format": "...",
  "description": "...",
  "audience": "..."
}}"""

        return await self.generate_json(prompt)

    async def generate_script(self, idea: str, duration: int = 45) -> str:
        """Genera un guion basado en una idea."""
        prompt = f"""Convierte esta idea en un guion para YouTube Shorts (máx {duration} segundos):

IDEA:
{idea}

Estructura requerida:
- Hook inicial fuerte (3-5 segundos)
- Desarrollo rápido con valor
- Final con CTA (call to action)

El guion debe:
- Ser conversacional y energético
- Aportar valor real
- Usar oraciones cortas
- Estar en español

Responde en JSON:
{{
  "hook": "...",
  "body": "...",
  "cta": "..."
}}"""

        return await self.generate_json(prompt)

    async def _generate_fallback(self, prompt: str) -> str:
        """Fallback cuando OpenRouter no está disponible."""
        logger.warning("⚠️ Fallback activado - usando mock script")

        try:
            from data.mock_script import get_mock_script
            mock = get_mock_script()
        except ImportError:
            mock = None

        prompt_lower = prompt.lower()

        if "guion" in prompt_lower or "script" in prompt.lower():
            if mock:
                return mock
            return """🎬 HOOK (0-3s):
"Esta inteligencia artificial ya está reemplazando trabajos… y probablemente ya la has usado."

📝 SCRIPT COMPLETO:
Esta inteligencia artificial ya está cambiando el mundo del trabajo, y lo más impactante es que probablemente ya la has usado.
[...]"""

        if "idea" in prompt.lower():
            import json
            import random
            idea = {
                "hook": "Esta IA ya está reemplazando trabajos",
                "format": "story",
                "description": "Contenido sobre inteligencia artificial y el futuro del trabajo",
                "audience": "general",
                "topic": "Inteligencia Artificial",
                "potential_views": random.randint(100000, 500000),
            }
            return json.dumps([idea], ensure_ascii=False)

        return mock or "Contenido de fallback"

    def is_available(self, provider: Optional[str] = None) -> bool:
        """Verifica si el servicio está disponible."""
        return self.client is not None

    def get_available_providers(self) -> Dict[str, bool]:
        """
        Retorna qué proveedores están disponibles.
        Siempre retorna solo OpenRouter.
        """
        return {
            "openrouter": self.client is not None,
        }

    def get_best_provider(self) -> Optional[str]:
        """Retorna el proveedor disponible."""
        return "openrouter" if self.client else None

    # =========================================
    # OBSERVABILIDAD
    # =========================================

    @classmethod
    def reset_counters(cls):
        """Resetea contadores entre ejecuciones."""
        logger.info("📊 Contadores de AI Service reseteados")

    @classmethod
    def get_stats(cls) -> dict:
        """Retorna estadísticas de uso."""
        return {
            "provider": "openrouter",
            "available": cls._instance is not None and cls._instance.client is not None,
        }
