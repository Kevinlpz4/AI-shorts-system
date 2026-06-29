"""
GenerateScriptUseCase — Caso de uso: generar un guion para un topic
=====================================================================
El usuario (o el sistema) solicita generar un guion para un ResearchTopic
que ya fue APROBADO.

Flujo:
  1. Buscar ResearchTopic por topic_id
  2. Validar que existe
  3. Validar que está APPROVED (no PENDING_REVIEW ni REJECTED)
  4. Validar que no existe ya un script (idempotencia — si existe, error)
  5. Convertir ResearchTopic → ContentIdea (bridge)
  6. Llamar ScriptGeneratorPort.generate_script()
  7. Validar Script.is_valid()
  8. Persistir script
  9. Retornar ScriptDTO

Errores que puede lanzar:
  - ResearchTopicNotFoundError (404) — topic no existe
  - ResearchError / ContentError si el topic no está APPROVED (HTTP 409)
  - ScriptAlreadyExistsError (409) — ya hay script para este topic
  - ScriptValidationError (422) — el guion generado no pasa validación
"""

import logging

from application.dtos.script import GenerateScriptRequest, ScriptDTO
from application.use_cases.script.mappers import research_topic_to_content_idea
from domain.exceptions.content import ContentError, ScriptValidationError
from domain.exceptions.script import ScriptAlreadyExistsError
from domain.ports.ai_provider import ScriptGeneratorPort
from domain.ports.script_repository import ScriptRepository
from research.domain.exceptions import ResearchTopicNotFoundError
from research.domain.ports.research_repository import ResearchRepository
from research.domain.value_objects.research_status import ResearchStatus

logger = logging.getLogger(__name__)


class GenerateScriptUseCase:
    """
    Caso de uso: generar guion para un topic aprobado.

    Dependencias:
      - research_repo: ResearchRepository (port)
      - script_repo: ScriptRepository (port)
      - ai_provider: ScriptGeneratorPort (port)
    """

    def __init__(
        self,
        research_repo: ResearchRepository,
        script_repo: ScriptRepository,
        ai_provider: ScriptGeneratorPort,
    ):
        self._research_repo = research_repo
        self._script_repo = script_repo
        self._ai_provider = ai_provider

    async def execute(
        self,
        request: GenerateScriptRequest,
    ) -> ScriptDTO:
        """
        Ejecuta la generación de guion.

        Args:
            request: GenerateScriptRequest con topic_id, duration, tone.

        Returns:
            ScriptDTO con el guion generado y persistido.

        Raises:
            ResearchTopicNotFoundError: si el topic no existe.
            ScriptAlreadyExistsError: si ya hay un guion para este topic.
            ScriptValidationError: si el guion generado no pasa validación.
        """
        topic_id = request.topic_id
        logger.info(
            "Generando guion para topic %s (duración=%s, tono=%s)",
            topic_id, request.duration, request.tone,
        )

        # 1. Buscar ResearchTopic
        topic = await self._research_repo.find_by_id(topic_id)
        if topic is None:
            raise ResearchTopicNotFoundError(
                topic_id=topic_id,
                detail=f"No se encontró topic con ID {topic_id}",
            )

        # 2. Validar que está APPROVED
        if topic.status != ResearchStatus.APPROVED:
            logger.warning(
                "Topic %s no está APPROVED (status=%s)",
                topic_id, topic.status.value,
            )
            raise ContentError(
                detail=f"El topic {topic_id} no está aprobado (status: {topic.status.value})",
            )

        # 3. Validar que no existe ya un script (idempotencia)
        existing = await self._script_repo.find_by_topic_id(topic_id)
        if existing is not None:
            logger.warning(
                "Ya existe un guion para topic %s (script=%s)",
                topic_id, existing.id,
            )
            raise ScriptAlreadyExistsError(
                topic_id=topic_id,
                detail=f"Ya existe un guion para el topic {topic_id}",
            )

        # 4. Bridge: ResearchTopic → ContentIdea
        idea = research_topic_to_content_idea(
            topic=topic,
            tone=request.tone,
        )

        # 5. Generar guion via IA
        logger.info("Generando guion via AI provider...")
        script = await self._ai_provider.generate_script(
            idea=idea,
            duration=request.duration,
            tone=request.tone,
        )

        # Conectar el script con el topic
        script.topic_id = topic_id
        script.tone = request.tone

        # 6. Validar calidad del guion
        if not script.is_valid():
            logger.error(
                "Guion generado no pasa validación: hook=%d, body=%d, cta=%d",
                len(script.hook), len(script.body), len(script.cta),
            )
            raise ScriptValidationError(
                detail=(
                    f"El guion generado no pasa validación "
                    f"(hook: {len(script.hook)} chars, "
                    f"body: {len(script.body)} chars, "
                    f"cta: {len(script.cta)} chars)"
                ),
            )

        # 7. Persistir
        await self._script_repo.save(script)
        logger.info("Guion %s guardado exitosamente para topic %s", script.id, topic_id)

        # 8. Retornar DTO
        return ScriptDTO.from_entity(script)
