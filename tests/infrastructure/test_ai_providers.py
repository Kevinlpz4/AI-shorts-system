"""
Tests para Proveedores de IA:
  - OpenRouterProvider (único provider real)
  - MockAIProvider (fallback para tests/desarrollo)
"""
import pytest
import os
from infrastructure.ai.openrouter_provider import OpenRouterProvider
from infrastructure.ai.mock_provider import MockAIProvider
from domain.exceptions.ai import InvalidProviderConfigError
from domain.ports.ai_provider import AIProvider


class TestOpenRouterProvider:
    """Tests para el único provider real: OpenRouter."""

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
            model="anthropic/claude-sonnet-4",
        )
        assert p.model == "anthropic/claude-sonnet-4"

    def test_supported_models_list(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert len(p.supported_models) > 0
        assert "openai/gpt-4o-mini" in p.supported_models

    def test_init_without_key_raises(self):
        with pytest.raises(InvalidProviderConfigError):
            OpenRouterProvider(api_key="")

    def test_init_with_custom_temperature(self):
        p = OpenRouterProvider(api_key="sk-test", temperature=0.5)
        assert p._temperature == 0.5

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
        """LSP: OpenRouterProvider debe cumplir con el Protocol AIProvider."""
        p = OpenRouterProvider(api_key="sk-or-v1-test")
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

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY"),
        reason="Requiere OPENROUTER_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_json_with_real_api(self):
        """generate_json con OpenRouter real (solo con -m integration)."""
        p = OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))
        result = await p.generate_json(
            'respondé SOLO con JSON: {"test": "ok"}'
        )
        assert isinstance(result, dict)
        assert result.get("test") == "ok"

    def test_parse_json(self):
        """Verifica que _parse_json extraiga correctamente JSON de texto."""
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        result = p._parse_json('{"clave": "valor"}')
        assert result == {"clave": "valor"}

        result = p._parse_json('Texto previo {"clave": "valor"} texto posterior')
        assert result == {"clave": "valor"}

        result = p._parse_json('[{"item": 1}]')
        assert result == {"items": [{"item": 1}]}

    def test_handle_error_mapping(self):
        """Los errores de API deben mapearse a excepciones de dominio."""
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        from domain.exceptions.ai import QuotaExceededError, RateLimitError, ProviderUnavailableError

        with pytest.raises(QuotaExceededError):
            p._handle_error(Exception("insufficient_quota"))
        with pytest.raises(QuotaExceededError):
            p._handle_error(Exception("429 quota exceeded"))
        with pytest.raises(RateLimitError):
            p._handle_error(Exception("rate limit exceeded"))
        with pytest.raises(ProviderUnavailableError):
            p._handle_error(Exception("connection error"))


class TestProviderInterface:
    """Verifica que TODOS los providers cumplan el Protocol AIProvider."""

    def test_mock_compatible(self):
        mock = MockAIProvider()
        assert isinstance(mock, AIProvider)

    def test_openrouter_compatible(self):
        p = OpenRouterProvider(api_key="sk-or-v1-test")
        assert isinstance(p, AIProvider)
