"""
ResearchRepository — Puerto para persistencia
===============================================
Define el contrato para guardar y recuperar ResearchTopics.

La implementación CONCRETA vive en research/infrastructure/persistence/.
Actualmente: SQLite.
Futuro: PostgreSQL, MongoDB, etc.

El dominio nunca conoce SQLite, ni tablas, ni queries.
Solo conoce este puerto.
"""

from typing import Optional, Protocol
from uuid import UUID

from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_status import ResearchStatus


class ResearchRepository(Protocol):
    """
    Protocol: repositorio de ResearchTopics.

    Trata a ResearchTopic como Aggregate Root.
    Siempre guarda/carga el agregado completo.
    """

    async def save(self, topic: ResearchTopic) -> None:
        """
        Guarda un topic (insert o update).

        Si el topic no existe → insert.
        Si existe → update completo del agregado.
        """
        ...

    async def save_many(self, topics: list[ResearchTopic]) -> None:
        """Guarda múltiples topics en una transacción."""
        ...

    async def find_by_id(self, topic_id: UUID) -> Optional[ResearchTopic]:
        """Busca un topic por su ID único."""
        ...

    async def find_by_status(
        self, status: ResearchStatus, limit: int = 50
    ) -> list[ResearchTopic]:
        """Busca topics por estado, ordenados por score descendente."""
        ...

    async def find_by_duplicate_hash(
        self, duplicate_hash: str
    ) -> list[ResearchTopic]:
        """Busca topics que compartan el mismo hash de duplicado."""
        ...

    async def find_pending_review(
        self, limit: int = 20
    ) -> list[ResearchTopic]:
        """
        Busca topics pendientes de revisión humana.
        Ordenados por score descendente (los mejores primero).
        """
        ...

    async def find_all(
        self, limit: int = 50, offset: int = 0
    ) -> list[ResearchTopic]:
        """Lista todos los topics, ordenados por fecha de creación descendente."""
        ...

    async def count_by_status(self, status: ResearchStatus) -> int:
        """Cuenta cuántos topics hay en un estado dado."""
        ...

    async def delete(self, topic_id: UUID) -> None:
        """Elimina un topic por ID."""
        ...
