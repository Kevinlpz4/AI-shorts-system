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
    
    # API Keys (desde variables de entorno)
    OPENAI_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    ANTHROPIC_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    GEMINI_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY")
    )
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
    
    # Proveedor de IA por defecto
    AI_PROVIDER: str = field(
        default_factory=lambda: os.getenv("AI_PROVIDER", "openai")
    )
    
    # Configuración de OpenAI (también compatible con OpenRouter)
    OPENAI_MODEL: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    OPENAI_BASE_URL: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL")
    )
    OPENAI_TEMPERATURE: float = 0.8
    OPENAI_MAX_TOKENS: int = 2000
    
    # Configuración de Anthropic (Claude)
    ANTHROPIC_MODEL: str = "claude-haiku-4-20250514"  # Haiku es el más barato
    ANTHROPIC_TEMPERATURE: float = 0.8
    ANTHROPIC_MAX_TOKENS: int = 2000
    
    # Configuración de Gemini
    GEMINI_MODEL: str = "gemini-2.0-flash-lite-001"  # El más barato y rápido
    GEMINI_TEMPERATURE: float = 0.8
    GEMINI_MAX_TOKENS: int = 2000
    
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
        """Valida que las configuraciones requeridas estén presentes."""
        required = ["OPENAI_API_KEY"]
        missing = [key for key in required if not getattr(self, key)]
        
        if missing:
            raise ValueError(f"Faltan configuraciones requeridas: {missing}")
        
        return True


# Instancia global de configuración
settings = Settings()