"""
ResearchSourcePort — Puerto para fuentes de investigación
===========================================================
Define el contrato que cualquier fuente externa debe implementar.

Cada adapter (GoogleNewsAdapter, TwitterAdapter, etc.) implementa este Protocol.

El dominio NUNCA conoce las implementaciones concretas.
Solo conoce este puerto.

Cómo agregar una nueva fuente (OCP ✅):
  1. Crear adapter en research/infrastructure/sources/
  2. Implementar ResearchSourcePort
  3. Registrar en SourceRegistry desde el Composition Root
  4. Nunca modificar domain/
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass(frozen=True)
class RawResearchData:
    """
    Datos crudos normalizados que devuelve cada fuente.

    Es un DTO de entrada al dominio (no una entidad).
    No tiene validación de negocio — solo transporta datos.
    El dominio valida cuando crea ResearchTopic.

    Atributos:
        title: Título de la noticia
        description: Resumen o descripción corta
        content: Contenido completo (si está disponible)
        url: URL original de la noticia
        author: Autor (si se conoce)
        published_at: Fecha de publicación (si se conoce)
    """
    title: str
    description: str = ""
    content: str = ""
    url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None


class ResearchSourcePort(Protocol):
    """
    Protocol: cualquier fuente de investigación debe implementar esto.

    Métodos requeridos:
        source_name: str — identificador único de la fuente
        available: bool — si la fuente está operativa
        fetch(query, limit) — obtiene resultados de investigación

    Tipado estructural (Protocol) — no requiere herencia explícita.
    """

    @property
    def source_name(self) -> str:
        """Nombre único de la fuente (ej: 'google-news', 'twitter')."""
        ...

    @property
    def available(self) -> bool:
        """Indica si la fuente está disponible actualmente."""
        ...

    async def fetch(
        self,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> list[RawResearchData]:
        """
        Obtiene resultados de investigación de la fuente.

        Args:
            query: Término de búsqueda (None = obtener trending/general)
            limit: Máximo de resultados

        Returns:
            Lista de datos crudos normalizados

        Raises:
            SourceNotAvailableError: si la fuente no está disponible
        """
        ...
