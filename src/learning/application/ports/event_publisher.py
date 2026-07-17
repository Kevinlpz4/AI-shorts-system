"""
EventPublisher Port — Abstracción de publicación de eventos de dominio.

Define el contrato para publicar DomainEvents después de que un aggregate
ha sido persistido exitosamente (después de commit).

La publicación SIEMPRE ocurre después de commit(), nunca antes.
Esto garantiza que si el commit falla, ningún evento se publica.

Uso::

    self._uow.commit()
    events = aggregate.pull_events()
    if events:
        self._event_publisher.publish_many(events)
"""

from __future__ import annotations

from typing import Protocol

from foundation.events.domain_event import DomainEvent


class EventPublisher(Protocol):
    """Publica eventos de dominio.

    Responsabilidades:
        - publish(): Publicar un único DomainEvent.
        - publish_many(): Publicar múltiples DomainEvents.

    NO hace:
        - No persiste eventos (eso es responsabilidad del EventStore).
        - No encola eventos (eso es responsabilidad del MessageBroker).
        - No maneja transacciones (commit ya ocurrió).

    NOTA: La implementación concreta DEBE ser resilient a fallos de
    publicación. Si la publicación falla, debe al menos registrar el
    error para reintento posterior (outbox pattern recomendado).
    """

    def publish(self, event: DomainEvent) -> None:
        """Publica un único evento de dominio.

        Args:
            event: El DomainEvent a publicar.
        """
        ...

    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publica múltiples eventos de dominio.

        Args:
            events: Lista de DomainEvents a publicar.
        """
        ...
