"""
AI Shorts System - Configuration
================================
Variables globales y configuración del sistema.

Único proveedor de IA: OpenRouter (https://openrouter.ai)
Los modelos se configuran via variables de entorno, NUNCA hardcodeados.
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
    # OpenRouter — Único proveedor de IA
    # ═══════════════════════════════════════════════
    # OpenRouter permite acceder a OpenAI, Anthropic, Google, Mistral, etc.
    # con UNA sola API key. Registrate en: https://openrouter.ai/keys
    OPENROUTER_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY")
    )
    OPENROUTER_MODEL: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL")
        or os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
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

    # ── Modelo por defecto (fallback para todos los casos de uso) ──
    DEFAULT_MODEL: str = field(
        default_factory=lambda: os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
    )

    # ── Modelos específicos por caso de uso ──
    # Si un modelo específico no está configurado, usa DEFAULT_MODEL
    MODEL_RESEARCH: str = field(
        default_factory=lambda: os.getenv("MODEL_RESEARCH", "")
    )
    MODEL_SCORING: str = field(
        default_factory=lambda: os.getenv("MODEL_SCORING", "")
    )
    MODEL_SCRIPT: str = field(
        default_factory=lambda: os.getenv("MODEL_SCRIPT", "")
    )
    MODEL_TITLE: str = field(
        default_factory=lambda: os.getenv("MODEL_TITLE", "")
    )
    MODEL_SUMMARY: str = field(
        default_factory=lambda: os.getenv("MODEL_SUMMARY", "")
    )

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
        Valida que la configuración requerida esté presente.
        
        OpenRouter es el ÚNICO proveedor de IA.
        Se requiere OPENROUTER_API_KEY.
        """
        if not self.OPENROUTER_API_KEY:
            raise ValueError(
                "Falta configuración requerida: OPENROUTER_API_KEY "
                "— registrate en https://openrouter.ai/keys"
            )
        
        return True


# Instancia global de configuración
settings = Settings()