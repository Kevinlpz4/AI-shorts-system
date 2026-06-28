"""
Research Persistence Adapters
==============================
Implementaciones concretas de ResearchRepository.

Adaptador incluido:
  - SQLiteResearchRepository: persistencia en SQLite
"""

from research.infrastructure.persistence.sqlite_repository import SQLiteResearchRepository

__all__ = [
    "SQLiteResearchRepository",
]
