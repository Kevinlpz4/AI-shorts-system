"""
AI Shorts System - Configuration
================================
Variables globales y configuración del sistema.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Settings:
    """Configuración global del sistema."""
    
    # Versión
    VERSION: str = "1.0.0"
    
    # Rutas base
    BASE_DIR: Path = Path(__file__).parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    
    # Directorios de assets
    AUDIO_DIR: Path = ASSETS_DIR / "audio"
    VIDEO_DIR: Path = ASSETS_DIR / "video"
    SUBTITLES_DIR: Path = ASSETS_DIR / "subtitles"
    OUTPUT_DIR: Path = ASSETS_DIR / "output"
    
    # ═══════════════════════════════════════════════
    # API Keys
    # ═══════════════════════════════════════════════

    # ── OpenRouter (PROVIDER PRIMARIO) ──
    # Usá OpenRouter como proxy para acceder a múltiples modelos
    # con UNA sola API key. Registrate en: https://openrouter.ai/keys
    OPENROUTER_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    OPENROUTER_MODEL: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    )
    OPENROUTER_BASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
    )
    OPENROUTER_TEMPERATURE: float = 0.8
    OPENROUTER_MAX_TOKENS: int = 2000
    OPENROUTER_REFERER: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_REFERER", "https://github.com/ai-shorts-system"
        )
    )
    OPENROUTER_TITLE: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_TITLE", "AI Shorts System")
    )

    # ── OpenAI Directo (FALLBACK / provider directo) ──
    # Solo necesario si NO usás OpenRouter.
    OPENAI_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    OPENAI_MODEL: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    OPENAI_BASE_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL")
    )
    OPENAI_TEMPERATURE: float = 0.8
    OPENAI_MAX_TOKENS: int = 2000

    # ── Anthropic Directo (provider directo opcional) ──
    ANTHROPIC_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    ANTHROPIC_MODEL: str = "claude-haiku-4-20250514"
    ANTHROPIC_TEMPERATURE: float = 0.8
    ANTHROPIC_MAX_TOKENS: int = 2000

    # ── Gemini Directo (provider directo opcional) ──
    GEMINI_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY")
    )
    GEMINI_MODEL: str = "gemini-2.0-flash-lite-001"
    GEMINI_TEMPERATURE: float = 0.8
    GEMINI_MAX_TOKENS: int = 2000

    # ── Otras APIs ──
    ELEVENLABS_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("ELEVENLABS_API_KEY")
    )
    YOUTUBE_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("YOUTUBE_API_KEY")
    )
    TWITTER_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("TWITTER_API_KEY")
    )
    NEWS_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("NEWS_API_KEY")
    )

    # ═══════════════════════════════════════════════
    # Proveedor activo
    # ═══════════════════════════════════════════════
    # Determina qué proveedor usa el Composition Root.
    # Valores: "openrouter" (default), "openai", "anthropic", "gemini", "mock"
    AI_PROVIDER: str = field(
        default_factory=lambda: os.getenv("AI_PROVIDER", "openrouter")
    )
    
    # Configuración de TTS
    TTS_PROVIDER: str = "elevenlabs"  # "elevenlabs" o "azure"
    TTS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel (español)
    TTS_SPEED: float = 1.0
    TTS_MODEL: str = "eleven_monolingual_v1"
    
    # Configuración de Video
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920  # 9:16 para shorts
    VIDEO_FPS: int = 30
    VIDEO_CODEC: str = "h264"
    VIDEO_BITRATE: str = "4M"
    
    # Configuración de Subtítulos
    SUBTITLES_FONT: str = "Arial"
    SUBTITLES_SIZE: int = 36
    SUBTITLES_COLOR: str = "white"
    SUBTITLES_BACKGROUND: str = "black"
    
    # Configuración de YouTube
    YOUTUBE_CHANNEL_ID: Optional[str] = field(
        default_factory=lambda: os.getenv("YOUTUBE_CHANNEL_ID")
    )
    YOUTUBE_VIDEO_CATEGORY: int = 28  # Science & Technology
    
    # Configuración de Pipeline
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 300
    ENABLE_CACHE: bool = True
    
    # ═══════════════════════════════════════════════
    # Database (PostgreSQL)
    # ═══════════════════════════════════════════════
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://kevin:1234@localhost:5432/system_shorts",
        )
    )

    # ═══════════════════════════════════════════════
    # Research Module
    # ═══════════════════════════════════════════════
    RESEARCH_DB_PATH: Path = DATA_DIR / "research.db"

    # Scheduler: descubrimiento automático de noticias
    RESEARCH_SCHEDULER_ENABLED: bool = field(
        default_factory=lambda: os.getenv("RESEARCH_SCHEDULER_ENABLED", "false").lower() == "true"
    )
    RESEARCH_SCHEDULER_INTERVAL: int = int(
        os.getenv("RESEARCH_SCHEDULER_INTERVAL", "60")  # minutos
    )
    RESEARCH_SCHEDULER_QUERIES: list = field(
        default_factory=lambda: [
            q.strip() for q in os.getenv("RESEARCH_SCHEDULER_QUERIES", "tecnología,inteligencia artificial,ciencia").split(",") if q.strip()
        ]
    )
    
    # ═══════════════════════════════════════════════
    # API Server
    # ═══════════════════════════════════════════════
    API_HOST: str = field(
        default_factory=lambda: os.getenv("API_HOST", "127.0.0.1")
    )
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_CORS_ORIGINS: list = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("API_CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
            if o.strip()
        ]
    )

    # Nichos disponibles
    AVAILABLE_NICHES: list = field(default_factory=lambda: [
        "tecnología",
        "negocios",
        "salud",
        "finanzas",
        "educación",
        "entretenimiento",
        "deportes",
        "moda",
        "comida",
        "viajes"
    ])
    
    # Formatos de contenido
    CONTENT_FORMATS: list = field(default_factory=lambda: [
        "story",      # Historia/narrativa
        "list",       # Lista (5 cosas...)
        "reaction",   # Reacción/opinión
        "tutorial",   # Tutorial/how-to
        "fact",       # Dato curioso
        "comparison", # Comparación
        "debunk"      # Desmentir mito
    ])
    
    # Tonos de contenido
    CONTENT_TONES: list = field(default_factory=lambda: [
        "educational",    # Educativo
        "entertaining",  # Entretenido
        "controversial", # Controversial
        "inspirational", # Inspirador
        "humor"         # Humor
    ])
    
    def __post_init__(self):
        """Crea los directorios necesarios si no existen."""
        for dir_path in [
            self.AUDIO_DIR,
            self.VIDEO_DIR,
            self.SUBTITLES_DIR,
            self.OUTPUT_DIR,
            self.DATA_DIR,
            self.MODELS_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """
        Valida que las configuraciones requeridas estén presentes
        según el proveedor de IA activo.
        
        - "openrouter" → OPENROUTER_API_KEY
        - "openai"     → OPENAI_API_KEY
        - "anthropic"  → ANTHROPIC_API_KEY
        - "gemini"     → GEMINI_API_KEY
        - "mock"       → no requiere API key
        """
        provider_key_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "mock": None,
        }
        
        required_key = provider_key_map.get(self.AI_PROVIDER)
        if required_key is None:
            # mock provider o desconocido — no validamos API key
            return True
        
        value = getattr(self, required_key, None)
        if not value:
            raise ValueError(
                f"Falta configuración requerida: {required_key} "
                f"(para provider activo: {self.AI_PROVIDER})"
            )
        
        return True


# Instancia global de configuración
settings = Settings()