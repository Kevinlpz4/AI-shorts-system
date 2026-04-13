"""
AI Shorts System - Services Package
===================================
Paquete de servicios externos.
"""

# Servicios principales
from .ai_service import AIService
from .tts_service import TTSService
from .news_service import NewsService
from .social_service import SocialService
from .youtube_service import YouTubeService

# backward compatibility
from .openai_service import OpenAIService  # DEPRECATED - usar AIService

__all__ = [
    "AIService",  # Servicio unificado (recomendado)
    "OpenAIService",  # Deprecated
    "TTSService",
    "NewsService",
    "SocialService",
    "YouTubeService"
]