"""
Research Persistence Adapters
==============================
Implementaciones concretas de repositorios de Research.

Adaptadores incluidos:
  - PostgresResearchRepository: persistencia en PostgreSQL via SQLAlchemy
  - PostgresSchedulerConfig: configuración del scheduler en PostgreSQL
"""

from research.infrastructure.persistence.postgres_repository import PostgresResearchRepository
from research.infrastructure.persistence.postgres_scheduler_config import PostgresSchedulerConfig

__all__ = [
    "PostgresResearchRepository",
    "PostgresSchedulerConfig",
]
