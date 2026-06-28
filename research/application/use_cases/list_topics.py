"""
ListTopicsUseCase — Caso de uso: listar topics
=================================================
Lista topics de investigación con filtros opcionales.

Útil para:
  - Mostrar topics pendientes de revisión
  - Historial de topics aprobados/rechazados
  - Dashboard / monitoreo
"""

from research.application.dtos import ListTopicsQuery, ResearchTopicDTO
from research.application.mappers import topic_to_dto
from research.domain.ports.research_repository import ResearchRepository
from research.domain.value_objects.research_status import ResearchStatus


class ListTopicsUseCase:
    """
    Caso de uso: listar topics con filtros.

    Dependencias:
      - repository: ResearchRepository (port)
    """

    def __init__(self, repository: ResearchRepository):
        self._repository = repository

    async def execute(self, query: ListTopicsQuery) -> list[ResearchTopicDTO]:
        """
        Lista topics según los filtros.

        Args:
            query: Filtros y paginación

        Returns:
            Lista de ResearchTopicDTO
        """
        if query.status:
            status = ResearchStatus(query.status)
            topics = await self._repository.find_by_status(
                status=status,
                limit=query.limit,
            )
        else:
            topics = await self._repository.find_all(
                limit=query.limit,
                offset=query.offset,
            )

        return [topic_to_dto(t) for t in topics]

    async def count_by_status(self) -> dict[str, int]:
        """
        Retorna conteo de topics por estado.

        Returns:
            Dict con cantidades por estado
        """
        counts = {}
        for status in ResearchStatus:
            count = await self._repository.count_by_status(status)
            counts[status.value] = count
        return counts

    async def get_pending_review(self, limit: int = 20) -> list[ResearchTopicDTO]:
        """
        Atajo: lista topics pendientes de revisión.

        Args:
            limit: Máximo de resultados

        Returns:
            Lista de topics pendientes, ordenados por score descendente
        """
        topics = await self._repository.find_pending_review(limit=limit)
        return [topic_to_dto(t) for t in topics]
