"""
Tests para OpenAIProvider (con y sin API key).
"""
import pytest
import os
from infrastructure.ai.openai_provider import OpenAIProvider
from domain.exceptions.ai import InvalidProviderConfigError


class TestOpenAIProvider:
    def test_init_without_key_raises(self):
        with pytest.raises(InvalidProviderConfigError):
            OpenAIProvider(api_key="")

    def test_init_with_key(self):
        p = OpenAIProvider(api_key="sk-test")
        assert p.name == "openai"
        assert p.available is True

    def test_init_with_base_url(self):
        p = OpenAIProvider(api_key="sk-test", base_url="https://openrouter.ai/api/v1")
        assert p.name == "openrouter"

    def test_init_with_custom_model(self):
        p = OpenAIProvider(api_key="sk-test", model="gpt-4")
        assert p._model == "gpt-4"

    def test_init_with_temperature(self):
        p = OpenAIProvider(api_key="sk-test", temperature=0.5)
        assert p._temperature == 0.5

    def test_available_without_client(self):
        """available debe ser True si client existe."""
        p = OpenAIProvider(api_key="sk-test")
        assert p.available is True

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requiere OPENAI_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_json_with_real_api(self):
        """Test de integración real (solo con API key configurada)."""
        p = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        result = await p.generate_json("respondé con JSON: {\"test\": \"ok\"}")
        assert isinstance(result, dict)

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requiere OPENAI_API_KEY en .env",
    )
    @pytest.mark.asyncio
    async def test_generate_with_real_api(self):
        p = OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        result = await p.generate("decí hola")
        assert isinstance(result, str)
        assert len(result) > 0


class TestProviderInterface:
    def test_mock_and_openai_conform_to_protocol(self):
        """Verifica compatibilidad con AIProvider Protocol."""
        from infrastructure.ai.mock_provider import MockAIProvider
        from domain.ports.ai_provider import AIProvider

        mock = MockAIProvider()
        assert isinstance(mock, AIProvider)
