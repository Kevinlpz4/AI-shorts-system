"""
AI Shorts System - Pipelines Package
=====================================
Paquete de pipelines de orquestación.
"""

from .content_pipeline import ContentPipeline
from .trends_pipeline import TrendsPipeline

__all__ = ["ContentPipeline", "TrendsPipeline"]