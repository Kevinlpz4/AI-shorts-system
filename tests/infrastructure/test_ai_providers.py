"""
Tests para Proveedores de IA:
  - OpenAICompatibleProvider (base genérico)
  - OpenRouterProvider (especializado, provider primario)
  - MockAIProvider (fallback)
"""
import pytest
import os
from infrastructure.ai.openai_compatible import OpenAICompatibleProvider
from infrastructure.ai.openrouter_provider import OpenRouterProvider
from infrastructure.ai.mock_provider import MockAIProvider
from domain.exceptions.ai import InvalidProviderConfigError
from domain.ports.ai_provider import AIProvider


class TestOpenAICompatibleProvider:
    """Tests para el provider BASE genérico."""

    def test_init_without_key_raises(self):
        with pytest.raises(InvalidProviderConfigError, match="API key no configurada"):
            OpenAICompatibleProvider(api_key="")

    def test_init_with_key(self):
        p = OpenAICompatibleProvider(api_key="sk-test")
        assert p.name == "openai-compatible"
        assert p.available is True

    def test_init_with_base_url(self):
        p = OpenAICompatibleProvider(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            provider_name="openrouter",
        )
        assert p.name == "openrouter"

    def test_init_with_custom_model(self):
        p = OpenAICompatibleProvider(api_key="sk-test", model="gpt-4")
        assert p.model == "gpt-4"

    def test_init_with_temperature(self):
        p = OpenAICompatibleProvider(api_key="sk-test", temperature=0.5)
        assert p._temperature == 0.5

    def test_available_without_client(self):
        """available debe ser True si el cliente existe."""
        p = OpenAICompatibleProvider(api_key="sk-test")
        assert p.available is True

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="Requiere OPENROUTER_API_KEY o OPENAI_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_with_real_openrouter(self):
        """Test de integración real con OpenRouter (solo con -m integration)."""
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        p = OpenAICompatibleProvider(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            provider_name="openrouter",
        )
        result = await p.generate("decí 'hola' en una palabra")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="Requiere OPENROUTER_API_KEY o OPENAI_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_json_with_real_api(self):
        """generate_json con OpenRouter real (solo con -m integration)."""
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        p = OpenAICompatibleProvider(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            provider_name="openrouter",
        )
        result = await p.generate_json(
            'respondé SOLO con JSON: {"test": "ok"}'
        )
        assert isinstance(result, dict)
        assert result.get("test") == "ok"

    def test_lsp_compatibility(self):
        """Verifica LSP: debe cumplir con el Protocol AIProvider."""
        p = OpenAICompatibleProvider(api_key="sk-test")
        assert isinstance(p, AIProvider)


class TestOpenRouterProvider:
    """Tests para el provider primario OpenRouter."""

    def test_init(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert p.name == "openrouter"
        assert p.available is True
        assert p.model == "openai/gpt-4o-mini"

    def test_default_base_url(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert p._base_url == "https://openrouter.ai/api/v1"

    def test_custom_model(self):
        p = OpenRouterProvider(
            api_key="sk-or-v1-test",
            model="anthropic/claude-3.5-haiku",
        )
        assert p.model == "anthropic/claude-3.5-haiku"

    def test_supported_models_list(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert len(p.supported_models) > 0
        assert "openai/gpt-4o-mini" in p.supported_models

    def test_init_without_key_raises(self):
        with pytest.raises(InvalidProviderConfigError):
            OpenRouterProvider(api_key="")

    def test_extra_headers_defaults(self):
        """Debe agregar HTTP-Referer y X-Title por defecto."""
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert "HTTP-Referer" in p._extra_headers
        assert "X-Title" in p._extra_headers

    def test_custom_extra_headers(self):
        p = OpenRouterProvider(
            api_key="sk-or-v1-test",
            extra_headers={"HTTP-Referer": "https://miproducto.com"},
        )
        assert p._extra_headers["HTTP-Referer"] == "https://miproducto.com"
        assert p._extra_headers["X-Title"] == "AI Shorts System"  # se mantiene default

    def test_lsp_compatibility(self):
        """LSP: OpenRouterProvider debe poder usarse donde va AIProvider."""
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert isinstance(p, OpenAICompatibleProvider)
        assert isinstance(p, AIProvider)

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY"),
        reason="Requiere OPENROUTER_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_with_real_api(self):
        """Test de integración real con OpenRouter (solo con -m integration)."""
        p = OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))
        result = await p.generate("decí 'hola' en una palabra")
        assert isinstance(result, str)
        assert len(result) > 0


class TestProviderInterface:
    """Verifica que TODOS los providers cumplan el Protocol."""

    def test_mock_compatible(self):
        mock = MockAIProvider()
        assert isinstance(mock, AIProvider)

    def test_openai_compatible(self):
        p = OpenAICompatibleProvider(api_key="sk-test")
        assert isinstance(p, AIProvider)

    def test_openrouter_compatible(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert isinstance(p, AIProvider)
