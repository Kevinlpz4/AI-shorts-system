"""
ApproveTopicUseCase — Caso de uso: aprobar un topic
======================================================
El usuario revisa un topic en PENDING_REVIEW y lo aprueba para
generación de contenido.

Flujo:
  1. Buscar topic por ID
  2. Llamar topic.approve() (validación de negocio en dominio)
  3. Guardar cambios
  4. Auto-generar script si corresponde (opcional)
  5. Retornar DTO con eventos

El dominio enforza que:
  - Solo se pueden aprobar topics en PENDING_REVIEW
  - Una vez APPROVED, no se puede cambiar

Auto-generate:
  - Si auto_generate=True → genera script
  - Si auto_generate=None y scheduler_config existe → usa scheduler_config.is_auto_generate_enabled()
  - Si ya existe script → skip (idempotente)
  - Si falla la generación → log error, NO revertir el approve
"""

import logging

from typing import Any, Callable, Optional

from research.application.dtos import ReviewDecisionDTO, ReviewResultDTO
from research.application.mappers import topic_to_dto, event_to_dict
from research.domain.ports.research_repository import ResearchRepository
from research.domain.exceptions import ResearchTopicNotFoundError

logger = logging.getLogger(__name__)


class ApproveTopicUseCase:
    """
    Caso de uso: aprobar un topic para generación de Short.

    Dependencias:
      - repository: ResearchRepository (port)
      - generate_script_uc: Callable opcional para auto-generar script
      - script_repo: Repositorio de scripts (opcional, para check de existencia)
      - scheduler_config: Config del scheduler (opcional, para auto_generate global)
    """

    def __init__(
        self,
        repository: ResearchRepository,
        generate_script_uc: Optional[Callable] = None,
        script_repo: Optional[Any] = None,
        scheduler_config: Optional[Any] = None,
    ):
        self._repository = repository
        self._generate_script_uc = generate_script_uc
        self._script_repo = script_repo
        self._scheduler_config = scheduler_config

    async def execute(
        self,
        dto: ReviewDecisionDTO,
        auto_generate: Optional[bool] = None,
    ) -> ReviewResultDTO:
        """
        Aprueba un topic, opcionalmente auto-genera script.

        Args:
            dto: ReviewDecisionDTO con topic_id
            auto_generate:
                - True → generar script siempre
                - None → usar scheduler_config.is_auto_generate_enabled() si está disponible
                - False → no generar

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

        # 2. Aprobar (dominio valida estado)
        topic.approve()

        # 3. Guardar
        await self._repository.save(topic)

        # 4. Determinar si debe auto-generar script
        should_generate = False
        if auto_generate is True:
            should_generate = True
        elif auto_generate is None and self._scheduler_config is not None:
            should_generate = self._scheduler_config.is_auto_generate_enabled()

        if should_generate:
            if not self._generate_script_uc or not self._script_repo:
                logger.warning(
                    "Auto-generate requested but generate_script_uc or script_repo not configured"
                )
            else:
                # Verificar si ya existe script (idempotencia)
                topic_id_str = str(topic.id)
                existing = await self._script_repo.find_by_topic_id(topic_id_str)
                if existing is not None:
                    logger.info(
                        "Script already exists for topic %s — skipping auto-generate",
                        topic_id_str,
                    )
                else:
                    try:
                        from application.dtos.script import GenerateScriptRequest

                        req = GenerateScriptRequest(
                            topic_id=topic_id_str,
                            duration=45,
                            tone="educational",
                        )
                        await self._generate_script_uc.execute(req)
                        logger.info(
                            "Auto-generated script for topic %s", topic_id_str
                        )
                    except Exception as e:
                        # NO revertir el approve — solo loguear el error
                        logger.exception(
                            "Auto-generate failed for topic %s: %s",
                            topic_id_str,
                            e,
                        )

        # 5. Extraer eventos y retornar
        events = topic.pull_events()

        return ReviewResultDTO(
            topic=topic_to_dto(topic),
            events=[event_to_dict(e) for e in events],
        )
