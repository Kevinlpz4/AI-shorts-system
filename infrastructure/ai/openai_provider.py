"""
⚠️ DEPRECADO — Usá OpenAICompatibleProvider en su lugar.

Este archivo se mantiene temporalmente para compatibilidad.
Migrá tus imports a infrastructure.ai.openai_compatible.

Razon del rename:
  OpenAIProvider era confuso — el provider NO es solo para OpenAI,
  funciona con CUALQUIER API compatible (OpenRouter, Azure, etc.).
"""

import logging
import warnings

from infrastructure.ai.openai_compatible import OpenAICompatibleProvider as OpenAIProvider

warnings.warn(
    "OpenAIProvider fue renombrado a OpenAICompatibleProvider. "
    "Actualizá tu import: "
    "from infrastructure.ai.openai_compatible import OpenAICompatibleProvider",
    DeprecationWarning,
    stacklevel=2,
)

logger = logging.getLogger(__name__)
logger.warning(
    "⚠️ [DEPRECADO] OpenAIProvider está en openai_provider.py. "
    "Migrá a OpenAICompatibleProvider en openai_compatible.py"
)

__all__ = ["OpenAIProvider"]
