"""
Common DTOs — tipos compartidos para respuestas de la API.

DTOs:
    - PaginatedDTO[T]: Envoltorio genérico para respuestas paginadas.
    - ResultDTO[T]: Envoltorio genérico para resultados operacionales.
    - ErrorDTO: Representación de un error de aplicación.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ErrorDTO:
    """Representación de un error de aplicación.

    Attributes:
        code: Código del error (ej: "RESOURCE_NOT_FOUND").
        message: Mensaje descriptivo del error.
        detail: Detalle adicional del error (opcional).
    """

    code: str
    message: str
    detail: str | None = None


@dataclass(frozen=True)
class ResultDTO(Generic[T]):
    """Envoltorio genérico para resultados operacionales.

    Attributes:
        success: Si la operación fue exitosa.
        data: Datos del resultado (presente si success=True).
        error: Información del error (presente si success=False).
    """

    success: bool
    data: T | None = None
    error: ErrorDTO | None = None


@dataclass(frozen=True)
class PaginatedDTO(Generic[T]):
    """Envoltorio para respuestas paginadas de la API.

    Attributes:
        items: Lista de DTOs de la página actual.
        total: Total de elementos en toda la colección.
        page: Página actual (1-indexed).
        size: Tamaño de página.
        pages: Total de páginas calculado redondeando hacia arriba.
    """

    items: tuple[T, ...]
    total: int
    page: int
    size: int
    pages: int
