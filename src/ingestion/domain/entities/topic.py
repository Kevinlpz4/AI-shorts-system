"""
Topic Entity — Tema o tópico de interés que guía la ingesta.

Topic es una Entity (NO Aggregate Root). Tiene identidad y ciclo de vida
simple. Es referenciado por ID desde NewsSource y Feed.

Invariantes:
  - I-22: name MUST NOT be empty
  - I-23: name MUST be unique across all Topics (enforced by repository)
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.base.entity import Entity

from ingestion.domain.entities.ids import TopicId
from ingestion.domain.exceptions import InvalidTopicError


@dataclass(eq=False)
class Topic(Entity):
    """Tema o tópico de interés.

    Attributes:
        id: Identidad única del topic.
        name: Nombre del topic, único globalmente.
        description: Descripción opcional del topic.
        is_active: Si está habilitado.
    """

    id: TopicId
    name: str
    description: str | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validar invariantes en construcción."""
        if not self.name or not self.name.strip():
            raise InvalidTopicError("Topic name must not be empty (I-22)")

    def rename(self, new_name: str) -> None:
        """Actualiza el nombre del topic.

        Args:
            new_name: Nuevo nombre.

        Raises:
            InvalidTopicError: Si el nuevo nombre está vacío.
        """
        if not new_name or not new_name.strip():
            raise InvalidTopicError("Topic name must not be empty (I-22)")
        self.name = new_name.strip()

    def update_description(self, desc: str | None) -> None:
        """Actualiza la descripción del topic.

        Args:
            desc: Nueva descripción o None para limpiarla.
        """
        self.description = desc

    def activate(self) -> None:
        """Marca el topic como activo."""
        self.is_active = True

    def deactivate(self) -> None:
        """Marca el topic como inactivo."""
        self.is_active = False
