"""
IntegrationEvent — Base class for cross-BC Integration Events.

IntegrationEvent extiende el concepto de DomainEvent para eventos
que CRUZAN Bounded Contexts. Difiere en:

    - source_boundary: OBLIGATORIO — qué BC publicó este evento
    - correlation_id: opcional — cadena de trazabilidad cross-BC
    - causation_id: opcional — qué DomainEvent originó este evento
    - event_version: obligatorio (default 1) para evolución controlada
    - event_name: PROPERTY calculada (type(self).__name__)
    - Payload: solo datos serializables (sin objetos de dominio)

No es una excepción. No contiene objetos de dominio. No asume formato
de serialización. No tiene lógica de enrutamiento.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from foundation.events._utcnow import _utcnow


@dataclass(frozen=True)
class IntegrationEvent:
    """
    Base class para Integration Events entre Bounded Contexts.

    DIFIERE de DomainEvent en:
        - ``source_boundary``: identifica qué BC publicó el evento
        - ``correlation_id``: cadena de trazabilidad cross-BC
        - ``causation_id``: qué DomainEvent originó este IntegrationEvent
        - ``event_version``: OBLIGATORIO (cambios incompatibles = breaking)
        - Payload serializable: solo tipos planos (str, int, dict, UUID, etc.)

    Responsabilidades:
        - Identidad única (event_id)
        - Nombre del evento (event_name) — inferido del nombre de clase
        - Source boundary (source_boundary)
        - Versionado estricto (event_version)
        - Trazabilidad (correlation_id, causation_id)
        - Timestamp (occurred_at)
        - Inmutabilidad total (frozen=True)

    NO hace:
        - No contiene objetos de dominio (EntityId, ValueObject, etc.)
        - No asume formato de serialización
        - No tiene lógica de enrutamiento
        - No se publica a sí mismo

    ¿Por qué source_boundary?
        - Sin source_boundary no se puede rutear ni filtrar eventos entre BCs.
        - Si bien el default es "" (string vacío), toda subclase DEBE setearlo.

    Uso en subclases:
        Los campos adicionales DEBEN tener default o ``field(default_factory=...)``
        para evitar el error de herencia de dataclasses:

            @dataclass(frozen=True)
            class TopicDiscoveredIntegration(IntegrationEvent):
                source_boundary: str = "research"
                topic_id: str = ""
                title: str = ""
    """

    event_id: UUID = field(default_factory=uuid4)
    event_version: int = 1
    source_boundary: str = ""
    correlation_id: str | None = None
    causation_id: UUID | None = None
    occurred_at: datetime = field(default_factory=_utcnow)

    @property
    def event_name(self) -> str:
        """
        Nombre del evento.

        Se calcula automáticamente del nombre de la clase concreta.
        No es un campo — es una propiedad computada.

        Returns:
            El nombre de la clase (ej: "TopicDiscoveredIntegration").
        """
        return type(self).__name__
