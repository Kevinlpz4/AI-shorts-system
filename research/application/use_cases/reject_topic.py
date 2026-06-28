"""
RejectTopicUseCase — Caso de uso: rechazar un topic
======================================================
El usuario revisa un topic en PENDING_REVIEW y lo rechaza.

Flujo:
  1. Buscar topic por ID
  2. Llamar topic.reject(reason) (validación de negocio en dominio)
  3. Guardar cambios
  4. Retornar DTO con eventos
"""

from research.application.dtos import ReviewDecisionDTO, ReviewResultDTO
from research.application.mappers import topic_to_dto, event_to_dict
from research.domain.ports.research_repository import ResearchRepository
from research.domain.exceptions import ResearchTopicNotFoundError


class RejectTopicUseCase:
    """
    Caso de uso: rechazar un topic.

    Dependencias:
      - repository: ResearchRepository (port)
    """

    def __init__(self, repository: ResearchRepository):
        self._repository = repository

    async def execute(self, dto: ReviewDecisionDTO) -> ReviewResultDTO:
        """
        Rechaza un topic.

        Args:
            dto: ReviewDecisionDTO con topic_id y razón opcional

        Returns:
            ReviewResultDTO con el topic actualizado y eventos
        """
        # 1. Buscar topic
        topic = await self._repository.find_by_id(dto.topic_id)
        if topic is None:
            raise ResearchTopicNotFoundError(
                topic_id=str(dto.topic_id),
                detail=f"No se encontró topic con ID {dto.topic_id}"
            )

        # 2. Rechazar (dominio valida estado)
        topic.reject(reason=dto.reject_reason)

        # 3. Guardar
        await self._repository.save(topic)

        # 4. Extraer eventos
        events = topic.pull_events()

        return ReviewResultDTO(
            topic=topic_to_dto(topic),
            events=[event_to_dict(e) for e in events],
        )
