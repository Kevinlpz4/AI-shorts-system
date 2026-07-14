"""
Topic Commands — operaciones CRUD y estado para Topic.

Commands:
    - CreateTopicCommand: Crear nuevo topic.
    - UpdateTopicCommand: Actualizar topic existente.
    - ActivateTopicCommand: Activar topic.
    - DeactivateTopicCommand: Desactivar topic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTopicCommand:
    """Crear un nuevo Topic.

    Attributes:
        name: Nombre del topic, único globalmente.
        description: Descripción opcional del topic.
    """

    name: str
    description: str | None = None


@dataclass(frozen=True)
class UpdateTopicCommand:
    """Actualizar un Topic existente.

    Todos los campos excepto ``topic_id`` son opcionales.
    Solo se actualizan los campos provistos (no None).

    Attributes:
        topic_id: ID del topic a actualizar.
        name: Nuevo nombre (opcional).
        description: Nueva descripción (opcional).
    """

    topic_id: str
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class ActivateTopicCommand:
    """Activar un Topic.

    Attributes:
        topic_id: ID del topic a activar.
    """

    topic_id: str


@dataclass(frozen=True)
class DeactivateTopicCommand:
    """Desactivar un Topic.

    Attributes:
        topic_id: ID del topic a desactivar.
    """

    topic_id: str
