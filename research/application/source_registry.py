"""
SourceRegistry — Registro de fuentes de investigación
========================================================
El Registry pattern permite registrar fuentes externas (adapters)
y consultarlas por nombre sin que el dominio conozca las implementaciones.

Técnicamente es parte de la capa de Application porque ORQUESTA
la selección de fuentes, pero no contiene lógica de negocio.

Responsabilidades:
  - Registrar fuentes (ResearchSourcePort implementations)
  - Recuperar fuentes por nombre
  - Listar fuentes disponibles/no disponibles
  - Validar que exista una fuente antes de usarla

Uso en Composition Root:
    registry = SourceRegistry()
    registry.register(GoogleNewsAdapter())
    registry.register(TwitterAdapter())

    # En un caso de uso:
    source = registry.get("google-news")
    results = await source.fetch(query="IA")
"""

from typing import Optional

from research.domain.ports.research_source import ResearchSourcePort
from research.domain.exceptions import SourceNotAvailableError


class SourceRegistry:
    """
    Registry de fuentes de investigación.

    Mantiene un dict interno nombre → adapter.
    Los adapters se registran desde el Composition Root.
    """

    def __init__(self):
        self._sources: dict[str, ResearchSourcePort] = {}

    def register(self, source: ResearchSourcePort) -> None:
        """
        Registra una fuente en el registry.

        Args:
            source: Implementación de ResearchSourcePort

        Raises:
            ValueError: si ya existe una fuente con ese nombre
        """
        name = source.source_name
        if name in self._sources:
            raise ValueError(
                f"Ya existe una fuente registrada con el nombre '{name}'"
            )
        self._sources[name] = source

    def get(self, name: str) -> ResearchSourcePort:
        """
        Obtiene una fuente por nombre.

        Args:
            name: Nombre único de la fuente

        Returns:
            Implementación de ResearchSourcePort

        Raises:
            SourceNotAvailableError: si la fuente no está registrada
        """
        source = self._sources.get(name)
        if source is None:
            raise SourceNotAvailableError(
                source_name=name,
                detail=f"No hay fuente registrada con el nombre '{name}'"
            )
        return source

    def get_all_available(self) -> list[ResearchSourcePort]:
        """
        Retorna todas las fuentes que están disponibles actualmente.

        Returns:
            Lista de fuentes disponibles
        """
        return [s for s in self._sources.values() if s.available]

    def list_sources(self) -> list[dict]:
        """
        Lista todas las fuentes registradas con su estado.

        Returns:
            Lista de dicts con name, available
        """
        return [
            {"name": name, "available": source.available}
            for name, source in self._sources.items()
        ]

    @property
    def count(self) -> int:
        """Cantidad de fuentes registradas."""
        return len(self._sources)

    def __contains__(self, name: str) -> bool:
        return name in self._sources
