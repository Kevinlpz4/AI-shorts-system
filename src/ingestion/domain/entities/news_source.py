"""
NewsSource — Aggregate Root del BC Ingestion.

Representa un origen externo de información (plataforma, sitio web, API).
Es el punto de entrada para la configuración de ingesta.

Ciclo de vida: Creado → Activo (is_active=True) → Inactivo (is_active=False)

Invariantes:
  - I-01: name MUST NOT be empty
  - I-02: name MUST be unique across all NewsSources (enforced by repository)
  - I-03: source_type MUST be a valid SourceType
  - I-04: source_url MUST be a valid URL (validated by SourceUrl VO)

Eventos emitidos:
  - SourceEnabled: cuando enable() es llamado exitosamente
  - SourceDisabled: cuando disable(reason) es llamado exitosamente

Cross-AR rules (Application Layer):
  - AL-01: No desactivar si tiene Feeds activos (verifica FeedRepository)
  - AL-02: Solo activar si tiene al menos un Feed activo
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from foundation.base.aggregate_root import AggregateRoot

from ingestion.domain.entities._categorizable import _Categorizable
from ingestion.domain.entities.ids import CategoryId, SourceId, TopicId
from ingestion.domain.events.ingestion_events import SourceDisabled, SourceEnabled
from ingestion.domain.exceptions import InvalidStateError
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl


@dataclass(eq=False, init=False)
class NewsSource(AggregateRoot, _Categorizable):
    """Fuente externa de información.

    Attributes:
        id: Identidad única del source.
        name: Nombre único y legible (ej: "Reddit", "Steam News").
        source_type: Tipo de fuente (RSS, API, SOCIAL_MEDIA, NEWSLETTER).
        source_url: URL base de la fuente.
        is_active: Si está habilitada para ingesta.
        categories: Categorías asignadas (M:N, referencias por ID).
        topics: Topics de interés que cubre (M:N, referencias por ID).
    """

    id: SourceId
    name: str
    source_type: SourceType
    source_url: SourceUrl
    is_active: bool = True
    categories: list[CategoryId] = field(default_factory=list)
    topics: list[TopicId] = field(default_factory=list)

    def __init__(
        self,
        id: SourceId,
        name: str,
        source_type: SourceType,
        source_url: SourceUrl,
        is_active: bool = True,
        categories: list[CategoryId] | None = None,
        topics: list[TopicId] | None = None,
    ) -> None:
        """Initialize a NewsSource.

        Args:
            id: Identidad única del source.
            name: Nombre único y legible.
            source_type: Tipo de fuente.
            source_url: URL base de la fuente.
            is_active: Si está habilitada para ingesta (default: True).
            categories: Categorías asignadas (default: []).
            topics: Topics de interés (default: []).

        Raises:
            InvalidStateError: Si name está vacío (I-01).
        """
        if not name or not name.strip():
            raise InvalidStateError("NewsSource name must not be empty (I-01)")

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name.strip())
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "is_active", is_active)
        object.__setattr__(self, "categories", categories or [])
        object.__setattr__(self, "topics", topics or [])
        # Initialize AggregateRoot._events
        object.__setattr__(self, "_events", [])

    def enable(self) -> None:
        """Marca como activo. Emite SourceEnabled.

        NOTA: AL-02 (requiere al menos un Feed activo) se verifica en
        Application Layer, no aquí.
        """
        self.is_active = True
        self.register_event(
            SourceEnabled(
                source_id=self.id,
                enabled_at=datetime.now(timezone.utc),
            )
        )

    def disable(self, reason: str) -> None:
        """Marca como inactivo con razón. Emite SourceDisabled.

        Args:
            reason: Razón de la deshabilitación.

        NOTA: AL-01 (no desactivar si tiene Feeds activos) se verifica en
        Application Layer, no aquí.
        """
        self.is_active = False
        self.register_event(
            SourceDisabled(
                source_id=self.id,
                reason=reason,
                disabled_at=datetime.now(timezone.utc),
            )
        )

    def change_url(self, new_url: SourceUrl) -> None:
        """Actualiza la URL base de la fuente.

        Args:
            new_url: Nueva URL (validada por SourceUrl VO).
        """
        self.source_url = new_url

    def change_source_type(self, new_type: SourceType) -> None:
        """Cambia el tipo de fuente.

        Args:
            new_type: Nuevo tipo de fuente.
        """
        self.source_type = new_type

    def assign_category(self, category_id: CategoryId) -> None:
        """Agrega una categoría a la fuente.

        No valida existencia de Category (consistencia eventual).
        """
        self._assign_category(self.categories, category_id)

    def remove_category(self, category_id: CategoryId) -> None:
        """Remueve una categoría de la fuente."""
        self._remove_category(self.categories, category_id)

    def assign_topic(self, topic_id: TopicId) -> None:
        """Agrega un topic a la fuente.

        No valida existencia de Topic (consistencia eventual).
        """
        self._assign_topic(self.topics, topic_id)

    def remove_topic(self, topic_id: TopicId) -> None:
        """Remueve un topic de la fuente."""
        self._remove_topic(self.topics, topic_id)
