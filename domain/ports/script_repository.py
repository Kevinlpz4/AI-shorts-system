"""
ScriptRepository — Puerto para persistencia de Scripts
========================================================
Define el contrato para guardar y recuperar Script entities.

La implementación CONCRETA vive en infrastructure/persistence/.
Actualmente: SQLite.
Futuro: PostgreSQL, etc.

El dominio nunca conoce SQLite, ni tablas, ni queries.
Solo conoce este puerto.
"""

from typing import Optional, Protocol

from domain.entities.script import Script


class ScriptRepository(Protocol):
    """
    Protocol: repositorio de Script entities.

    Trata a Script como Aggregate Root.
    """

    async def save(self, script: Script) -> None:
        """
        Guarda un script (insert o update).

        Si el script no existe → insert.
        Si existe → update completo.
        """
        ...

    async def find_by_topic_id(self, topic_id: str) -> Optional[Script]:
        """
        Busca un script por topic_id.

        Args:
            topic_id: ID del ResearchTopic asociado.

        Returns:
            Script si existe, None si no.
        """
        ...

    async def delete_by_topic_id(self, topic_id: str) -> None:
        """
        Elimina un script por topic_id.

        Args:
            topic_id: ID del ResearchTopic asociado.
        """
        ...
