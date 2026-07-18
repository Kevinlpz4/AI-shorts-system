"""
InMemory Event Bus implementations for Learning BC integration.

Provides InMemory adapters for all four integration event bus ports:
    - InMemoryIntegrationEventBus: outbound (publishes IntegrationEvents)
    - InMemoryIngestionEventBus: inbound (subscribes to Ingestion events)
    - InMemoryResearchEventBus: inbound (subscribes to Research events)
    - InMemoryPublicationEventBus: inbound (subscribes to Publication events)

These implementations are for testing only. The inbound buses include
a ``publish()`` helper method (NOT part of the Protocol) to simulate
incoming events during tests.
"""
from __future__ import annotations

from typing import Callable

from foundation.events.integration_event import IntegrationEvent


class InMemoryIntegrationEventBus:
    """Outbound event bus — accumulates IntegrationEvents.

    Implements the IntegrationEventBus Protocol for testing.
    Events are stored in a list for inspection after the operation
    under test has completed.

    Usage::

        bus = InMemoryIntegrationEventBus()
        bus.publish(SomeEvent(source_boundary="learning"))
        assert len(bus.published_events) == 1
        bus.clear()
    """

    def __init__(self) -> None:
        self._events: list[IntegrationEvent] = []

    def publish(self, event: IntegrationEvent) -> None:
        """Publish a single integration event."""
        self._events.append(event)

    def publish_many(self, events: list[IntegrationEvent]) -> None:
        """Publish multiple integration events atomically."""
        self._events.extend(events)

    @property
    def published_events(self) -> list[IntegrationEvent]:
        """Return a copy of all published events."""
        return list(self._events)

    def clear(self) -> None:
        """Clear all accumulated events."""
        self._events.clear()


class InMemoryIngestionEventBus:
    """Inbound event bus for Ingestion BC events.

    Implements the IngestionEventBus Protocol for testing.
    Includes a ``publish()`` helper to simulate incoming events —
    this method is NOT part of the Protocol but is essential for
    testing event-driven flows.

    Usage::

        bus = InMemoryIngestionEventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))
        bus.start()
        bus.publish(some_event)
        assert len(received) == 1
    """

    def __init__(self) -> None:
        self._handlers: list[Callable] = []
        self._running = False
        self._events_received: list[IntegrationEvent] = []

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Ingestion events."""
        self._handlers.append(handler)

    def unsubscribe(self, handler: Callable) -> None:
        """Unsubscribe a previously subscribed handler.

        Raises:
            ValueError: If the handler was not subscribed.
        """
        self._handlers.remove(handler)

    def start(self) -> None:
        """Start listening for events."""
        self._running = True

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False

    def publish(self, event: IntegrationEvent) -> None:
        """Dispatch event to all handlers (test helper, NOT in Protocol)."""
        self._events_received.append(event)
        for handler in self._handlers:
            handler(event)

    @property
    def is_running(self) -> bool:
        """Whether the bus is currently running."""
        return self._running

    @property
    def handler_count(self) -> int:
        """Number of subscribed handlers."""
        return len(self._handlers)


class InMemoryResearchEventBus:
    """Inbound event bus for Research BC events.

    Implements the ResearchEventBus Protocol for testing.
    Includes a ``publish()`` helper to simulate incoming events.

    Usage::

        bus = InMemoryResearchEventBus()
        bus.subscribe(my_handler)
        bus.start()
        bus.publish(some_event)
    """

    def __init__(self) -> None:
        self._handlers: list[Callable] = []
        self._running = False
        self._events_received: list[IntegrationEvent] = []

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Research events."""
        self._handlers.append(handler)

    def unsubscribe(self, handler: Callable) -> None:
        """Unsubscribe a previously subscribed handler.

        Raises:
            ValueError: If the handler was not subscribed.
        """
        self._handlers.remove(handler)

    def start(self) -> None:
        """Start listening for events."""
        self._running = True

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False

    def publish(self, event: IntegrationEvent) -> None:
        """Dispatch event to all handlers (test helper, NOT in Protocol)."""
        self._events_received.append(event)
        for handler in self._handlers:
            handler(event)

    @property
    def is_running(self) -> bool:
        """Whether the bus is currently running."""
        return self._running

    @property
    def handler_count(self) -> int:
        """Number of subscribed handlers."""
        return len(self._handlers)


class InMemoryPublicationEventBus:
    """Inbound event bus for Publication BC events.

    Implements the PublicationEventBus Protocol for testing.
    Includes a ``publish()`` helper to simulate incoming events.

    Usage::

        bus = InMemoryPublicationEventBus()
        bus.subscribe(my_handler)
        bus.start()
        bus.publish(some_event)
    """

    def __init__(self) -> None:
        self._handlers: list[Callable] = []
        self._running = False
        self._events_received: list[IntegrationEvent] = []

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Publication events."""
        self._handlers.append(handler)

    def unsubscribe(self, handler: Callable) -> None:
        """Unsubscribe a previously subscribed handler.

        Raises:
            ValueError: If the handler was not subscribed.
        """
        self._handlers.remove(handler)

    def start(self) -> None:
        """Start listening for events."""
        self._running = True

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False

    def publish(self, event: IntegrationEvent) -> None:
        """Dispatch event to all handlers (test helper, NOT in Protocol)."""
        self._events_received.append(event)
        for handler in self._handlers:
            handler(event)

    @property
    def is_running(self) -> bool:
        """Whether the bus is currently running."""
        return self._running

    @property
    def handler_count(self) -> int:
        """Number of subscribed handlers."""
        return len(self._handlers)
