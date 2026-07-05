"""
Source Queries — consultas para NewsSource.

Queries:
    - FindSourceQuery: Buscar fuente por ID.
    - ListActiveSourcesQuery: Listar todas las fuentes activas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindSourceQuery:
    """Buscar un NewsSource por su ID.

    Attributes:
        source_id: ID de la fuente a buscar.
    """

    source_id: str


@dataclass(frozen=True)
class ListActiveSourcesQuery:
    """Listar todas las fuentes activas del sistema.

    Sin filtros adicionales (YAGNI — se agregan cuando se necesiten).
    """
