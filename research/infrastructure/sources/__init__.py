"""
Research Source Adapters
========================
Implementaciones concretas de ResearchSourcePort.

Cada adapter:
  - Implementa el protocolo ResearchSourcePort
  - Conoce la API externa (Google News, Twitter, etc.)
  - Traduce resultados a RawResearchData
  - Nunca es importado por el dominio

Adapters incluidos:
  - MockResearchSource: datos simulados para testing y desarrollo
  - GoogleNewsRSSSource: feed RSS público de Google News (sin API key)
"""

from research.infrastructure.sources.mock_source import MockResearchSource
from research.infrastructure.sources.google_news_rss import GoogleNewsRSSSource

__all__ = [
    "MockResearchSource",
    "GoogleNewsRSSSource",
]
