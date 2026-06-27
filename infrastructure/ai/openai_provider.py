import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from domain.exceptions.ai import (
    QuotaExceededError,
    ProviderUnavailableError,
    RateLimitError,
    InvalidProviderConfigError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    Proveedor de IA usando OpenAI API (también compatible con OpenRouter).
    
    Puerto que implementa: AIProvider (domain/ports/ai_provider.py)
    
    OpenRouter permite usar modelos de OpenAI, Anthropic, Google, etc.
    con una sola API key y una API compatible con OpenAI.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 2000,
    ):
        if not api_key:
            raise InvalidProviderConfigError("OPENAI_API_KEY no configurada")

        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._name = "openai"

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            self._name = "openrouter"

        self._client = AsyncOpenAI(**client_kwargs)
        logger.info(f"✅ {self._name.title()} client inicializado (modelo: {model})")

    @property
    def name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return self._client is not None

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Genera texto usando el modelo configurado."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "Sos un experto en contenido viral para YouTube Shorts. Respondé siempre en español."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["quota", "429", "insufficient_quota", "payment"]):
                raise QuotaExceededError(str(e))
            if any(x in error_msg for x in ["rate", "too many"]):
                raise RateLimitError(str(e))
            raise ProviderUnavailableError(str(e))

    async def generate_json(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Genera respuesta JSON."""
        json_prompt = prompt + "\n\n⚠️ Respondé SOLO con JSON válido, sin explicaciones."
        response = await self.generate(
            prompt=json_prompt,
            temperature=temperature or 0.7,
            max_tokens=max_tokens or self._max_tokens,
        )
        return self._parse_json(response)

    def _parse_json(self, text: str) -> dict:
        """Parsea JSON de la respuesta."""
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
