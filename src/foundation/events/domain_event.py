"""
DomainEvent — Base class for intra-BC Domain Events.

DomainEvent es un ``@dataclass(frozen=True)`` que provee:
    - event_id: UUID único del evento (auto-generado)
    - event_version: versión del schema del evento
    - occurred_at: timestamp UTC de ocurrencia (auto-generado)
    - event_name: PROPERTY calculada que retorna ``type(self).__name__``

No es una excepción. No se publica a sí mismo. No persiste.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from foundation.events._utcnow import _utcnow


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class para Domain Events intra-BC.

    Responsabilidades:
        - Identidad única (event_id)
        - Timestamp de ocurrencia (occurred_at)
        - Nombre del evento (event_name) — inferido del nombre de clase
        - Versionado (event_version)
        - Inmutabilidad total (frozen=True)

    NO hace:
        - No tiene lógica de negocio
        - No se publica a sí mismo
        - No se persiste (es transitorio)

    ¿Por qué event_name es @property?
        - Elimina la necesidad de __post_init__ para auto-asignación
        - Garantiza que el nombre SIEMPRE coincida con la clase
        - Evita problemas de herencia de dataclasses con defaults
        - No requiere object.__setattr__ en objetos frozen

    ¿Por qué frozen=True?
        - Un evento es un hecho consumado. No se puede modificar el pasado.
        - Inmutabilidad garantiza que los handlers ven datos consistentes.

    ¿Por qué event_version?
        - Los eventos evolucionan. El versionado permite cambios controlados.
        - Subclases incrementan event_version si cambian el schema.

    Uso en subclases:
        Los campos adicionales DEBEN tener default o ``field(default_factory=...)``
        para evitar el error de herencia de dataclasses:

            @dataclass(frozen=True)
            class TopicDiscovered(DomainEvent):
                topic_id: UUID = field(default_factory=uuid4)
                title: str = ""
    """

    event_id: UUID = field(default_factory=uuid4)
    event_version: int = 1
    occurred_at: datetime = field(default_factory=_utcnow)

    @property
    def event_name(self) -> str:
        """
        Nombre del evento.

        Se calcula automáticamente del nombre de la clase concreta.
        No es un campo — es una propiedad computada.
        Esto garantiza que el nombre SIEMPRE refleje la clase real.

        Returns:
            El nombre de la clase (ej: "TopicDiscovered", "FeedAdded").
        """
        return type(self).__name__
