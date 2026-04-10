"""
AI Shorts System - Application Package
======================================
Punto de entrada y configuración global de la aplicación.
"""

__version__ = "1.0.0"
__author__ = "AI Shorts Team"

from .config import settings
from .logger import logger

__all__ = ["settings", "logger"]