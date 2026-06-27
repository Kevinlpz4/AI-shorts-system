"""
Composition Root — Fábrica de dependencias
============================================
TODO el wiring de dependencias en UN solo lugar.
Si cambiás un provider, lo cambiás SOLO acá.
"""
import logging
from typing import Optional

from app.config import settings

# ── Domain ──
from domain.services.content_evaluator import ContentEvaluator

# ── Infrastructure ──
from infrastructure.ai.openai_provider import OpenAIProvider
from infrastructure.ai.mock_provider import MockAIProvider
from infrastructure.tts.mock_provider import MockTTSProvider
from infrastructure.cache.memory_cache import MemoryCache
from infrastructure.persistence.file_repository import FileRepository
from infrastructure.trends.mock_source import MockTrendSource
from infrastructure.publishing.mock_publisher import MockPublisher
from infrastructure.video.mock_renderer import MockVideoRenderer

# ── Application ──
from application.use_cases.generate_content import GenerateContentUseCase
from application.use_cases.evaluate_content import EvaluateContentUseCase
from application.use_cases.manage_trends import ManageTrendsUseCase

logger = logging.getLogger(__name__)


class Container:
    """
    Contenedor de dependencias.
    
    Crea y conecta TODAS las dependencias del sistema.
    Centraliza la configuración para facilitar cambios.
    """
    
    def __init__(self):
        # ── Cache ──
        self.cache = MemoryCache(default_ttl=1800)

        # ── Persistencia ──
        self.repository = FileRepository(data_dir=str(settings.DATA_DIR))

        # ── Evaluador de contenido (dominio puro) ──
        self.evaluator = ContentEvaluator()

        # ── Proveedores de IA ──
        self._init_ai_providers()

        # ── TTS ──
        self.tts_provider = MockTTSProvider(output_dir=str(settings.AUDIO_DIR))

        # ── Video ──
        self.video_renderer = MockVideoRenderer(output_dir=str(settings.VIDEO_DIR))

        # ── Trends ──
        self.trend_sources = [
            MockTrendSource(source_type="news"),
            MockTrendSource(source_type="twitter"),
            MockTrendSource(source_type="youtube"),
        ]

        # ── Publisher ──
        self.publisher = MockPublisher(platform_name="youtube")

        # ── Use Cases ──
        self._init_use_cases()

        logger.info("✅ Container: todas las dependencias inicializadas")

    def _init_ai_providers(self):
        """Inicializa proveedores de IA."""
        self.ai_provider = self._create_primary_ai()
        self.fallback_ai = MockAIProvider()

    def _create_primary_ai(self):
        """Crea el proveedor de IA principal según configuración."""
        provider = settings.AI_PROVIDER

        if provider == "openai":
            try:
                return OpenAIProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    base_url=settings.OPENAI_BASE_URL,
                    temperature=settings.OPENAI_TEMPERATURE,
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                )
            except Exception as e:
                logger.warning(f"⚠️ OpenAI no disponible: {e}. Usando fallback.")
                return MockAIProvider()

        logger.info(f"Proveedor {provider} no implementado, usando fallback")
        return MockAIProvider()

    def _init_use_cases(self):
        """Inicializa casos de uso con todas las dependencias."""
        # El AIProvider primario + fallback envuelto
        ai = self._create_fallback_ai_wrapper()

        self.generate_content = GenerateContentUseCase(
            ai_provider=ai,
            tts_provider=self.tts_provider,
            video_renderer=self.video_renderer,
            repository=self.repository,
            trend_sources=self.trend_sources,
            publisher=self.publisher,
            cache=self.cache,
            evaluator=self.evaluator,
        )

        self.evaluate_content = EvaluateContentUseCase(
            evaluator=self.evaluator,
            repository=self.repository,
        )

        self.manage_trends = ManageTrendsUseCase(
            sources=self.trend_sources,
            repository=self.repository,
            cache=self.cache,
        )

    def _create_fallback_ai_wrapper(self):
        """
        Crea wrapper que intenta proveedor primario y cae a fallback.
        
        Esto implementa el patrón Chain of Responsibility
        sin modificar los providers individuales (OCP ✅).
        """
        primary = self.ai_provider
        fallback = self.fallback_ai

        class FallbackAIWrapper:
            """Wrapper que intenta primario → fallback."""

            @property
            def name(self) -> str:
                return f"{primary.name}+{fallback.name}"

            @property
            def available(self) -> bool:
                return True

            async def generate(self, prompt: str, **kwargs) -> str:
                try:
                    if primary.available:
                        return await primary.generate(prompt, **kwargs)
                except Exception as e:
                    logger.warning(f"⚠️ {primary.name} falló: {e}. Usando fallback.")
                return await fallback.generate(prompt, **kwargs)

            async def generate_json(self, prompt: str, **kwargs) -> dict:
                try:
                    if primary.available:
                        return await primary.generate_json(prompt, **kwargs)
                except Exception as e:
                    logger.warning(f"⚠️ {primary.name} falló (json): {e}. Usando fallback.")
                return await fallback.generate_json(prompt, **kwargs)

        return FallbackAIWrapper()
