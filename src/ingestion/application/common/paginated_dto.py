"""
PaginatedDTO[T] — envoltorio para respuestas paginadas de la API.

Diferencia con ``QueryResult``:
    - ``QueryResult`` se usa INTERNAMENTE en la aplicación (service → presentación).
    - ``PaginatedDTO`` es para respuestas de API (serialización externa).

``PaginatedDTO`` incluye un cálculo automático de ``pages``
basado en ``total`` y ``size``.

Uso::

    from ingestion.application.common import PaginatedDTO

    page = PaginatedDTO(
        data=[source_summary_dto],
        total=42,
        page=1,
        size=50,
    )

    assert page.pages == 1  # 42 items, 50 per page → 1 page
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PaginatedDTO(Generic[T]):
    """Envoltorio para respuestas paginadas.

    Attributes:
        data: Lista de DTOs de la página actual.
        total: Total de elementos en toda la colección.
        page: Página actual (1-indexed).
        size: Tamaño de página.

    Properties:
        pages: Total de páginas calculado redondeando hacia arriba.
    """

    data: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        """Calcula el total de páginas.

        Returns:
            Número total de páginas (0 si total es 0).
        """
        if self.total == 0:
            return 0
        return (self.total + self.size - 1) // self.size
