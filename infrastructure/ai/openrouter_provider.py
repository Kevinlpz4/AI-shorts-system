"""
OpenRouterProvider — Proveedor PRIMARIO de IA
==============================================
OpenRouter es un proxy que permite acceder a múltiples modelos de IA
(OpenAI, Anthropic, Google, Mistral, etc.) con UNA sola API key y
UNA API compatible con OpenAI.

Ventajas de tenerlo como provider primario:
  1️⃣ Una sola API key para todos los modelos
  2️⃣ Fallback automático entre modelos si uno falla
  3️⃣ Costos más bajos (paga por lo que usa, sin suscripción fija)

Si en el futuro querés agregar un proveedor DIRECTO (ej. Anthropic directo),
creá una nueva clase en infrastructure/ai/ que implemente AIProvider.
No necesitás modificar nada de esto.

Uso:
    provider = OpenRouterProvider(api_key="sk-or-v1-...")
    result = await provider.generate("Hola")

Modelos recomendados:
  - openai/gpt-4o-mini         → rápido, barato, buena calidad
  - anthropic/claude-3.5-haiku → rápido, excelente para español
  - google/gemini-2.0-flash-001 → gratis (mientras tenga cuota)
"""

import logging
from typing import Optional

from infrastructure.ai.openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(OpenAICompatibleProvider):
    """
    Proveedor PRIMARIO de IA usando OpenRouter.

    OpenRouter usa API compatible con OpenAI, así que extendemos
    OpenAICompatibleProvider. Solo cambiamos:
    - Defaults específicos de OpenRouter (URL, modelo, headers)
    - Headers HTTP-Referer y X-Title para tracking

    🔧 Para cambiar de modelo: solo cambiá la env OPENROUTER_MODEL
       Ej: "anthropic/claude-3.5-haiku" o "google/gemini-2.0-flash-001"

    🆕 Para agregar un proveedor DIRECTO después:
        class AnthropicDirectProvider:
            '''Implementa AIProvider.'''
            async def generate(self, prompt, **kwargs) -> str:
                ...
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.8,
        max_tokens: int = 2000,
        extra_headers: Optional[dict] = None,
    ):
        """
        Inicializa el proveedor de OpenRouter.

        Args:
            api_key: API key de OpenRouter (sk-or-v1-...)
            model: Modelo formateado como "proveedor/modelo"
                   Ej: "openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"
            base_url: Endpoint de OpenRouter
            temperature: Temperatura de generación (0.0-1.0)
            max_tokens: Máximo de tokens por respuesta
            extra_headers: Headers adicionales HTTP-Referer / X-Title
        """
        self._extra_headers = extra_headers or {}
        if "HTTP-Referer" not in self._extra_headers:
            self._extra_headers["HTTP-Referer"] = "https://github.com/ai-shorts-system"
        if "X-Title" not in self._extra_headers:
            self._extra_headers["X-Title"] = "AI Shorts System"

        logger.info(
            "🔗 OpenRouter: %s | modelo: %s | headers: %s",
            base_url,
            model,
            bool(self._extra_headers),
        )

        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            provider_name="openrouter",
        )

    def _build_client(self) -> None:
        """
        Crea el cliente AsyncOpenAI con headers de OpenRouter.

        OpenRouter requiere HTTP-Referer y recomienda X-Title
        para aparecer en los rankings públicos de providers.
        """
        client_kwargs: dict = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        if self._extra_headers:
            client_kwargs["default_headers"] = self._extra_headers

        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(**client_kwargs)

    @property
    def supported_models(self) -> list[str]:
        """
        Modelos recomendados para OpenRouter.
        Lista completa: https://openrouter.ai/models
        """
        return [
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-haiku",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-001",
            "mistral/mistral-small",
            "meta-llama/llama-3.2-3b",
        ]
