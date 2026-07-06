"""SQLAlchemyEventPublisher — In-memory Domain Event publisher.

Stores events in memory for testing/verification. No external IO.
Prepared for Outbox evolution (Sprint 5.5).
Implements EventPublisher Protocol from application.ports.
"""

from __future__ import annotations

from foundation.events.domain_event import DomainEvent
from ingestion.application.ports.event_publisher import EventPublisher


class SQLAlchemyEventPublisher:
    """In-memory event publisher.

    Stores ALL published events in ``self.events`` for inspection.
    No external IO. Implements EventPublisher Protocol.

    Attributes:
        events: All events published so far, in insertion order.
    """

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        """Publish a single Domain Event. Stores in memory.

        Args:
            event: The DomainEvent to publish.
        """
        self.events.append(event)

    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple Domain Events preserving order.

        Args:
            events: DomainEvents to publish.
        """
        self.events.extend(events)
