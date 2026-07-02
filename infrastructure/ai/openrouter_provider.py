"""
OpenRouterProvider — Único proveedor de IA del sistema
========================================================
OpenRouter es un proxy que permite acceder a MÚLTIPLES modelos de IA
(OpenAI, Anthropic, Google, Mistral, etc.) con UNA sola API key y
UNA API compatible con OpenAI.

Arquitectura:
  - Puerto que implementa: AIProvider (domain/ports/ai_provider.py)
  - NO depende de ningún otro adaptador concreto
  - Se inyecta via Dependency Injection en el Composition Root

Uso:
    provider = OpenRouterProvider(api_key="sk-or-v1-...")
    result = await provider.generate("Hola")

Modelos configurables via env vars (NUNCA hardcodeados):
  OPENROUTER_API_KEY  — API key de OpenRouter
  OPENROUTER_MODEL    — Modelo default (ej: "openai/gpt-4o-mini")
  MODEL_RESEARCH      — Modelo para investigación
  MODEL_SCORING       — Modelo para scoring
  MODEL_SCRIPT        — Modelo para generación de guiones
  MODEL_TITLE         — Modelo para títulos
  MODEL_SUMMARY       — Modelo para resúmenes
"""

import json
import logging
from typing import Optional, Any

from openai import AsyncOpenAI

from domain.exceptions.ai import (
    QuotaExceededError,
    ProviderUnavailableError,
    RateLimitError,
    InvalidProviderConfigError,
)

logger = logging.getLogger(__name__)


class OpenRouterProvider:
    """
    Proveedor ÚNICO de IA usando OpenRouter.

    Puerto que implementa: AIProvider (domain/ports/ai_provider.py)

    OpenRouter usa API compatible con OpenAI, por lo que usamos
    el SDK de OpenAI para comunicarnos. La selección del PROVEEDOR
    desaparece — siempre usamos OpenRouter. La selección del MODELO
    permanece configurable via variables de entorno.

    Para cambiar el modelo:
        OPENROUTER_MODEL=anthropic/claude-sonnet-4
        OPENROUTER_MODEL=google/gemini-2.5-pro
        OPENROUTER_MODEL=deepseek/deepseek-chat
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        temperature: float = 0.8,
        max_tokens: int = 2000,
        provider_name: str = "openrouter",
        extra_headers: Optional[dict] = None,
    ):
        if not api_key:
            raise InvalidProviderConfigError(
                "API key de OpenRouter no configurada. "
                "Setéá OPENROUTER_API_KEY en .env"
            )

        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._name = provider_name
        self._api_key = api_key
        self._base_url = base_url
        self._extra_headers = extra_headers or {}

        # Headers requeridos por OpenRouter
        if "HTTP-Referer" not in self._extra_headers:
            self._extra_headers["HTTP-Referer"] = "https://github.com/ai-shorts-system"
        if "X-Title" not in self._extra_headers:
            self._extra_headers["X-Title"] = "AI Shorts System"

        self._client: Optional[AsyncOpenAI] = None
        self._build_client()

        logger.info(
            "🔗 OpenRouter inicializado (modelo: %s | base: %s)",
            model,
            base_url,
        )

    def _build_client(self) -> None:
        """Crea el cliente AsyncOpenAI con headers de OpenRouter."""
        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        if self._extra_headers:
            client_kwargs["default_headers"] = self._extra_headers
        self._client = AsyncOpenAI(**client_kwargs)

    # ── Properties ──────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Nombre del proveedor."""
        return self._name

    @property
    def model(self) -> str:
        """Modelo activo."""
        return self._model

    @property
    def available(self) -> bool:
        """Siempre True si se inicializó correctamente."""
        return self._client is not None

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

    # ── Generate ────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Genera texto usando OpenRouter.

        Args:
            prompt: Prompt de entrada
            temperature: Temperatura (0.0-1.0). Usa default si no se especifica.
            max_tokens: Máximo de tokens. Usa default si no se especifica.

        Returns:
            Texto generado

        Raises:
            QuotaExceededError: Sin créditos disponibles
            RateLimitError: Demasiadas requests
            ProviderUnavailableError: Error del proveedor
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sos un experto en contenido viral para YouTube Shorts. "
                            "Respondé siempre en español."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            self._handle_error(e)

    async def generate_json(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Genera respuesta en formato JSON.

        Args:
            prompt: Prompt de entrada
            temperature: Temperatura (usa default si no se especifica)
            max_tokens: Máximo de tokens (usa default si no se especifica)

        Returns:
            Diccionario parseado desde JSON
        """
        json_prompt = (
            prompt + "\n\n⚠️ Respondé SOLO con JSON válido, sin explicaciones."
        )
        response = await self.generate(
            prompt=json_prompt,
            temperature=temperature or 0.7,
            max_tokens=max_tokens or self._max_tokens,
        )
        return self._parse_json(response)

    # ── Helpers ─────────────────────────────────────────────────

    def _handle_error(self, error: Exception) -> None:
        """
        Mapea errores de la API a excepciones de dominio.

        Los errores de OpenRouter son los mismos que los de OpenAI
        por ser API compatible.
        """
        error_msg = str(error).lower()

        if any(
            x in error_msg
            for x in ["quota", "429", "insufficient_quota", "payment"]
        ):
            raise QuotaExceededError(str(error))
        if any(x in error_msg for x in ["rate", "too many"]):
            raise RateLimitError(str(error))

        raise ProviderUnavailableError(str(error))

    def _parse_json(self, text: str) -> dict:
        """
        Parsea JSON de la respuesta del modelo.

        Busca el primer { } o [ ] en el texto y lo parsea.
        """
        try:
            # Buscar array [...] primero (para que [{"a":1}] no se coma el { interno)
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end != 0:
                return {"items": json.loads(text[start:end])}

            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])

        except json.JSONDecodeError:
            logger.warning("No se pudo parsear JSON de la respuesta")

        return {}
