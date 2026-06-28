"""
OpenAICompatibleProvider — Proveedor BASE para APIs compatibles con OpenAI
==========================================================================
Este es el provider genérico para CUALQUIER API que use el formato OpenAI:
  - OpenAI directo
  - OpenRouter (proxy multi-modelo)
  - Cualquier API compatible con el SDK de OpenAI

Cumple con el puerto AIProvider (domain/ports/ai_provider.py).
Sigue el Principio de Sustitución de Liskov (LSP): cualquier subclase
puede reemplazar a esta clase sin romper el sistema.

Uso:
    provider = OpenAICompatibleProvider(
        api_key="sk-...",
        model="gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",  # opcional
    )
    result = await provider.generate("Hola")
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


class OpenAICompatibleProvider:
    """
    Proveedor BASE para APIs compatibles con OpenAI.

    Puerto que implementa: AIProvider (domain/ports/ai_provider.py)
    Soporta: OpenAI directo, OpenRouter, Azure OpenAI, etc.

    Para crear un proveedor específico (OCP ✅):
        1. Heredá de esta clase
        2. Sobrescribí _build_client() si necesitás config especial
        3. O simplemente cambiales los defaults en tu __init__

    Ejemplo:
        class MiProveedor(OpenAICompatibleProvider):
            def __init__(self, api_key, **kwargs):
                kwargs.setdefault("model", "mi-modelo")
                kwargs.setdefault("base_url", "https://api.miprov.com/v1")
                super().__init__(api_key=api_key, **kwargs)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 2000,
        provider_name: str = "openai-compatible",
    ):
        if not api_key:
            raise InvalidProviderConfigError(
                "API key no configurada para proveedor OpenAI-compatible"
            )

        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._name = provider_name

        self._api_key = api_key
        self._base_url = base_url
        self._build_client()

        logger.info(
            "✅ %s client inicializado (modelo: %s)",
            self._name.title(),
            model,
        )

    def _build_client(self) -> None:
        """
        Crea el cliente AsyncOpenAI.

        Las subclases pueden SOBRESCRIBIR este método para:
        - Agregar headers personalizados (como OpenRouter)
        - Usar un cliente diferente pero compatible
        - Inyectar configuración extra

        Esto respeta OCP: la clase base no se modifica,
        las subclases extienden el comportamiento. ✅
        """
        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        self._client = AsyncOpenAI(**client_kwargs)

    # ── Properties ──────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Nombre del proveedor (usado para identificar en logs)."""
        return self._name

    @property
    def model(self) -> str:
        """Modelo activo."""
        return self._model

    @property
    def available(self) -> bool:
        """Siempre True si se inicializó correctamente."""
        return self._client is not None

    # ── Generate ────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Genera texto usando el modelo configurado.

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

        Cada proveedor directo puede sobrescribir este método
        para manejar errores específicos de su API.
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
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])

            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end != 0:
                return {"items": json.loads(text[start:end])}

        except json.JSONDecodeError:
            logger.warning("No se pudo parsear JSON de la respuesta")

        return {}
