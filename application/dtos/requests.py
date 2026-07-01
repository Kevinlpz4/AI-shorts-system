"""
Request DTOs — Data Transfer Objects para solicitudes
======================================================
Requests para los casos de uso legacy.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerateContentRequest:
    """Request para generar contenido."""
    niche: Optional[str] = None
    platform: str = "youtube"
    count: int = 1
    duration: int = 45
    tone: str = "educational"
    trend_sources: list[str] = field(default_factory=lambda: ["news", "twitter", "youtube"])


@dataclass
class EvaluateRequest:
    """Request para evaluar contenido."""
    content_type: str = "idea"  # idea | script
    content_id: str = ""
    optimize: bool = True


@dataclass
class TrendRequest:
    """Request para obtener tendencias."""
    niche: Optional[str] = None
    sources: list[str] = field(default_factory=lambda: ["news", "twitter", "youtube"])
    limit: int = 20


@dataclass
class PublishRequest:
    """Request para publicar video."""
    video_id: str = ""
    platform: str = "youtube"
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
