"""
QueryResult[T] — resultado paginado de una consulta.

Envoltorio genérico que encapsula el resultado de una consulta
junto con metadata de paginación. Evita repetir ``total``,
``page``, ``size`` en cada DTO de lista.

Uso::

    from learning.application.common import QueryResult

    result = QueryResult(
        data=[feedback_summary_dto],
        total=42,
        page=1,
        size=50,
    )

    for item in result.data:
        ...
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class QueryResult(Generic[T]):
    """Resultado de una consulta con metadata de paginación.

    Attributes:
        data: Lista de resultados (tipo T).
        total: Total de resultados disponibles (para paginación).
        page: Página actual (1-indexed).
        size: Tamaño de página solicitado.
    """

    data: list[T]
    total: int | None = None
    page: int | None = None
    size: int | None = None
