"""
Composition Root — Fábrica de dependencias
============================================
TODO el wiring de dependencias en UN solo lugar.
Si cambiás una implementación, lo cambiás SOLO acá.

Sigue DIP: el contenedor registra implementaciones concretas del puerto
AIProvider (domain/ports/ai_provider.py). Application y Domain
NO saben qué implementación concreta se usa.
"""
import logging
from typing import Optional

from app.config import settings

# ── Domain ──
from domain.services.content_evaluator import ContentEvaluator

# ── Infrastructure ──
from infrastructure.ai.openrouter_provider import OpenRouterProvider
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

# ── Research Module ──
from research.infrastructure.persistence.postgres_repository import PostgresResearchRepository
from research.infrastructure.persistence.postgres_scheduler_config import PostgresSchedulerConfig
from research.infrastructure.sources.google_news_rss import GoogleNewsRSSSource
from research.infrastructure.sources.mock_source import MockResearchSource
from research.application.source_registry import SourceRegistry
from research.domain.services.duplicate_detector import (
    CompositeDuplicateDetector,
    UrlNormalizerStrategy,
    TitleNormalizerStrategy,
)
from research.domain.services.research_scorer import ResearchScorer
from research.application.use_cases.auto_discover import AutoDiscoverTopicsUseCase
from research.application.use_cases.manual_input import RegisterManualInputUseCase
from research.application.use_cases.approve_topic import ApproveTopicUseCase
from research.application.use_cases.reject_topic import RejectTopicUseCase
from research.application.use_cases.list_topics import ListTopicsUseCase
from research.application.scheduler import ResearchScheduler

logger = logging.getLogger(__name__)


class FallbackAIWrapper:
    """
    Wrapper que intenta un provider primario y cae a MockAIProvider.
    
    Implementa duck-typing compatible con AIProvider, IdeaGeneratorPort
    y ScriptGeneratorPort (domain/ports/ai_provider.py).
    
    Chain of Responsibility: primario → fallback.
    """

    def __init__(self, primary: Optional[OpenRouterProvider], fallback: MockAIProvider):
        self._primary = primary
        self._fallback = fallback

    @property
    def name(self) -> str:
        if self._primary:
            return f"{self._primary.name}+{self._fallback.name}"
        return self._fallback.name

    @property
    def available(self) -> bool:
        return True

    async def generate(self, prompt: str, **kwargs) -> str:
        """Intenta primario → fallback."""
        if self._primary and self._primary.available:
            try:
                return await self._primary.generate(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️ {self._primary.name} falló: {e}. Usando fallback.")
        return await self._fallback.generate(prompt, **kwargs)

    async def generate_json(self, prompt: str, **kwargs) -> dict:
        """Intenta primario → fallback (JSON)."""
        if self._primary and self._primary.available:
            try:
                return await self._primary.generate_json(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"⚠️ {self._primary.name} falló (json): {e}. Usando fallback.")
        return await self._fallback.generate_json(prompt, **kwargs)

    async def generate_script(self, idea, duration=45, tone="educational"):
        """
        Genera script: intenta primario (si tiene generate_script) → fallback.
        
        OpenRouterProvider NO implementa generate_script (usa generate_json),
        así que por ahora siempre cae a MockAIProvider para scripts.
        """
        if self._primary and hasattr(self._primary, 'generate_script'):
            try:
                if self._primary.available:
                    return await self._primary.generate_script(
                        idea=idea, duration=duration, tone=tone
                    )
            except Exception as e:
                logger.warning(
                    f"⚠️ {self._primary.name} falló (script): {e}. Usando fallback."
                )
        return await self._fallback.generate_script(
            idea=idea, duration=duration, tone=tone
        )


class Container:
    """
    Contenedor de dependencias.
    
    Crea y conecta TODAS las dependencias del sistema.
    Centraliza la configuración para facilitar cambios.
    
    DIP: el contenedor conoce las implementaciones concretas,
    pero Application y Domain solo ven los puertos (Protocols).
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

        # ── Research ──
        self._init_research()

        # ── Use Cases ──
        self._init_use_cases()

        logger.info("✅ Container: todas las dependencias inicializadas")

    # ═══════════════════════════════════════════════
    # AI Providers
    # ═══════════════════════════════════════════════

    def _init_ai_providers(self):
        """
        Inicializa proveedores de IA.
        
        Único provider real: OpenRouter (vía OpenRouterProvider).
        Fallback: MockAIProvider para desarrollo/testing.
        
        Cada caso de uso puede tener un modelo específico configurable
        via env vars (MODEL_RESEARCH, MODEL_SCRIPT, etc.).
        Si no se configura, usa DEFAULT_MODEL.
        """
        self.fallback_ai = MockAIProvider()

        # Providers wrapped con fallback para cada caso de uso
        self._ai_research = self._build_wrapped_provider(
            model=settings.MODEL_RESEARCH or settings.DEFAULT_MODEL,
        )
        self._ai_scoring = self._build_wrapped_provider(
            model=settings.MODEL_SCORING or settings.DEFAULT_MODEL,
        )
        self._ai_script = self._build_wrapped_provider(
            model=settings.MODEL_SCRIPT or settings.DEFAULT_MODEL,
        )
        self._ai_title = self._build_wrapped_provider(
            model=settings.MODEL_TITLE or settings.DEFAULT_MODEL,
        )
        self._ai_summary = self._build_wrapped_provider(
            model=settings.MODEL_SUMMARY or settings.DEFAULT_MODEL,
        )

        # Default provider (backwards compat)
        self.ai_provider = self._ai_research

    def _build_wrapped_provider(self, model: str) -> FallbackAIWrapper:
        """
        Crea un OpenRouterProvider envuelto con fallback a MockAIProvider.
        
        Este método es reutilizable por subclases (ApiContainer).
        Si OpenRouter no está disponible, retorna solo el fallback.
        
        Args:
            model: Modelo a usar (ej: "openai/gpt-4o-mini", "anthropic/claude-sonnet-4")
        """
        primary = None
        if settings.OPENROUTER_API_KEY:
            try:
                primary = OpenRouterProvider(
                    api_key=settings.OPENROUTER_API_KEY,
                    model=model,
                    base_url=settings.OPENROUTER_BASE_URL,
                    temperature=settings.OPENROUTER_TEMPERATURE,
                    max_tokens=settings.OPENROUTER_MAX_TOKENS,
                    extra_headers={
                        "HTTP-Referer": settings.OPENROUTER_REFERER,
                        "X-Title": settings.OPENROUTER_TITLE,
                    },
                )
            except Exception as e:
                logger.warning(
                    "⚠️ OpenRouter no disponible para modelo '%s': %s. Usando fallback.",
                    model, e,
                )
        else:
            logger.warning(
                "⚠️ OPENROUTER_API_KEY no configurada. Usando fallback MockAIProvider."
            )

        return FallbackAIWrapper(primary=primary, fallback=self.fallback_ai)

    # ═══════════════════════════════════════════════
    # Research Module
    # ═══════════════════════════════════════════════

    def _init_research(self):
        """Inicializa módulo Research (descubrimiento + scheduler)."""
        # ── Persistencia (PostgreSQL via SQLAlchemy) ──
        self.research_repository = PostgresResearchRepository()
        self.scheduler_config = PostgresSchedulerConfig()

        # ── Source Registry ──
        self.research_source_registry = SourceRegistry()
        self.research_source_registry.register(GoogleNewsRSSSource(locale="es-419"))
        self.research_source_registry.register(MockResearchSource())

        # ── Domain Services ──
        self.research_duplicate_detector = CompositeDuplicateDetector([
            UrlNormalizerStrategy(),
            TitleNormalizerStrategy(),
        ])
        self.research_scorer = ResearchScorer()

        # ── Use Cases ──
        self.register_manual_input = RegisterManualInputUseCase(
            repository=self.research_repository,
            duplicate_detector=self.research_duplicate_detector,
        )
        self.auto_discover_topics = AutoDiscoverTopicsUseCase(
            repository=self.research_repository,
            source_registry=self.research_source_registry,
            duplicate_detector=self.research_duplicate_detector,
            scorer=self.research_scorer,
        )
        self.approve_topic = ApproveTopicUseCase(
            repository=self.research_repository,
        )
        self.reject_topic = RejectTopicUseCase(
            repository=self.research_repository,
        )
        self.list_topics = ListTopicsUseCase(
            repository=self.research_repository,
        )

        # ── Scheduler ──
        self.research_scheduler = ResearchScheduler(
            auto_discover_use_case=self.auto_discover_topics,
            config=self.scheduler_config,
        )

        logger.info("📰 Research module initialized (scheduler: %s)",
                     "ON" if self.scheduler_config.is_enabled() else "OFF")

    # ═══════════════════════════════════════════════
    # Use Cases
    # ═══════════════════════════════════════════════

    def _init_use_cases(self):
        """Inicializa casos de uso con todas las dependencias."""
        self.generate_content = GenerateContentUseCase(
            ai_provider=self._ai_research,
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
