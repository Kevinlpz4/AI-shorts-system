"""
InMemoryLearningEventPublisher — publisher de eventos en memoria para testing.

Acumula los eventos publicados en una lista para inspección posterior.
Es ideal para verificar que los eventos correctos se publican durante
las operaciones de los servicios.

Uso::

    publisher = InMemoryLearningEventPublisher()
    publisher.publish(event)
    assert publisher.has_event(SomeEvent)
    assert len(publisher.published_events) == 1
    publisher.clear()
"""
from __future__ import annotations

from foundation.events.domain_event import DomainEvent


class InMemoryLearningEventPublisher:
    """EventPublisher en memoria que almacena eventos para inspección.

    Attributes:
        _events: Lista interna de eventos publicados.
    """

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        """Publica un único evento de dominio.

        Args:
            event: El DomainEvent a publicar.
        """
        self._events.append(event)

    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publica múltiples eventos de dominio.

        Args:
            events: Lista de DomainEvents a publicar.
        """
        self._events.extend(events)

    @property
    def published_events(self) -> list[DomainEvent]:
        """Retorna una copia de la lista de eventos publicados."""
        return list(self._events)

    def has_event(self, event_type: type) -> bool:
        """Verifica si al menos un evento del tipo dado fue publicado.

        Args:
            event_type: Clase del evento a buscar (ej: ``FeedbackCaptured``).

        Returns:
            ``True`` si al menos un evento de ese tipo fue publicado.
        """
        return any(isinstance(e, event_type) for e in self._events)

    def clear(self) -> None:
        """Limpia todos los eventos acumulados."""
        self._events.clear()
