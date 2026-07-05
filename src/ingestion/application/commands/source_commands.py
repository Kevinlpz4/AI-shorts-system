"""
Source Commands — operaciones CRUD y de estado para NewsSource.

Commands:
    - RegisterSourceCommand: Crear nueva fuente.
    - UpdateSourceCommand: Actualizar datos de fuente existente.
    - EnableSourceCommand: Habilitar fuente.
    - DisableSourceCommand: Deshabilitar fuente con razón.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterSourceCommand:
    """Crear una nueva fuente externa.

    Attributes:
        name: Nombre único y legible de la fuente.
        source_type: Tipo de fuente (RSS, API, SOCIAL_MEDIA, NEWSLETTER).
        source_url: URL base de la fuente.
    """

    name: str
    source_type: str
    source_url: str


@dataclass(frozen=True)
class UpdateSourceCommand:
    """Actualizar datos de una fuente existente.

    Todos los campos excepto ``source_id`` son opcionales.
    Solo se actualizan los campos provistos (no None).

    Attributes:
        source_id: ID de la fuente a actualizar.
        name: Nuevo nombre (opcional).
        source_type: Nuevo tipo de fuente (opcional).
        source_url: Nueva URL base (opcional).
    """

    source_id: str
    name: str | None = None
    source_type: str | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class EnableSourceCommand:
    """Habilitar una fuente para ingesta.

    Attributes:
        source_id: ID de la fuente a habilitar.
    """

    source_id: str


@dataclass(frozen=True)
class DisableSourceCommand:
    """Deshabilitar una fuente con razón.

    La validación AL-01 (no deshabilitar si tiene Feeds activos)
    se realiza en el Service.

    Attributes:
        source_id: ID de la fuente a deshabilitar.
        reason: Razón de la deshabilitación.
    """

    source_id: str
    reason: str
