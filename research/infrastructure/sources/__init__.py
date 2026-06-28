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
"""

from research.infrastructure.sources.mock_source import MockResearchSource

__all__ = [
    "MockResearchSource",
]
