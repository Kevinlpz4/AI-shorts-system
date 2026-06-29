"""
GetScriptUseCase — Caso de uso: obtener un guion por topic_id
================================================================
Consulta si existe un guion para un ResearchTopic dado.

Flujo:
  1. Buscar script por topic_id
  2. Si existe → retornar ScriptDTO
  3. Si no existe → retornar None

Útil para:
  - Mostrar el guion en la UI cuando el topic está APPROVED
  - Verificar si ya existe antes de generar
"""

import logging
from typing import Optional

from application.dtos.script import ScriptDTO
from domain.ports.script_repository import ScriptRepository

logger = logging.getLogger(__name__)


class GetScriptUseCase:
    """
    Caso de uso: obtener guion por topic_id.

    Dependencias:
      - script_repo: ScriptRepository (port)
    """

    def __init__(self, script_repo: ScriptRepository):
        self._script_repo = script_repo

    async def execute(self, topic_id: str) -> Optional[ScriptDTO]:
        """
        Busca un guion por topic_id.

        Args:
            topic_id: ID del ResearchTopic.

        Returns:
            ScriptDTO si existe, None si no.
        """
        script = await self._script_repo.find_by_topic_id(topic_id)
        if script is None:
            logger.info("No se encontró guion para topic %s", topic_id)
            return None

        logger.debug("Guion encontrado para topic %s (script=%s)", topic_id, script.id)
        return ScriptDTO.from_entity(script)
