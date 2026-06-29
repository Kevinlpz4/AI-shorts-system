"""
RegenerateScriptUseCase — Caso de uso: regenerar un guion
============================================================
El usuario solicita regenerar un guion existente para un topic.
Elimina el guion anterior y genera uno nuevo.

Flujo:
  1. Eliminar script existente (si existe)
  2. Delegar en GenerateScriptUseCase para generar el nuevo
  3. Retornar ScriptDTO

Útil para:
  - El usuario no está conforme con el guion generado
  - Se cambiaron los parámetros (duración, tono)
"""

import logging

from application.dtos.script import GenerateScriptRequest, ScriptDTO
from application.use_cases.script.generate_script import GenerateScriptUseCase
from domain.ports.script_repository import ScriptRepository

logger = logging.getLogger(__name__)


class RegenerateScriptUseCase:
    """
    Caso de uso: regenerar guion para un topic.

    Dependencias:
      - script_repo: ScriptRepository (port) — para eliminar el existente
      - _generate_uc: GenerateScriptUseCase — para generar el nuevo
    """

    def __init__(
        self,
        script_repo: ScriptRepository,
        generate_uc: GenerateScriptUseCase,
    ):
        self._script_repo = script_repo
        self._generate_uc = generate_uc

    async def execute(
        self,
        request: GenerateScriptRequest,
    ) -> ScriptDTO:
        """
        Regenera un guion: elimina el existente y genera uno nuevo.

        Args:
            request: GenerateScriptRequest con topic_id, duration, tone.

        Returns:
            ScriptDTO con el nuevo guion generado y persistido.
        """
        topic_id = request.topic_id
        logger.info("Regenerando guion para topic %s", topic_id)

        # 1. Eliminar script existente
        existing = await self._script_repo.find_by_topic_id(topic_id)
        if existing is not None:
            logger.info(
                "Eliminando guion existente %s para topic %s",
                existing.id, topic_id,
            )
            await self._script_repo.delete_by_topic_id(topic_id)

        # 2. Delegar en GenerateScriptUseCase
        return await self._generate_uc.execute(request)
