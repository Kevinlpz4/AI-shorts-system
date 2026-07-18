"""
Integration Event Bus Ports — Protocol-based ports for cross-BC event communication.

These ports define the contracts for event publishing and subscribing.
No concrete implementations — adapters implement these protocols.
"""
from __future__ import annotations

from typing import Callable, Protocol

from foundation.events.integration_event import IntegrationEvent


class IntegrationEventBus(Protocol):
    """Port for publishing integration events to other BCs.

    Learning publishes outbound events (RecommendationGenerated, etc.)
    through this port. The adapter decides how to deliver them
    (in-memory, message queue, event store, etc.).
    """

    def publish(self, event: IntegrationEvent) -> None:
        """Publish a single integration event."""
        ...

    def publish_many(self, events: list[IntegrationEvent]) -> None:
        """Publish multiple integration events atomically."""
        ...


class IngestionEventBus(Protocol):
    """Port for subscribing to Ingestion BC events.

    Learning subscribes to Ingestion events (RawArticleCollected, etc.)
    through this port. The adapter manages the subscription lifecycle.
    """

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Ingestion events."""
        ...

    def start(self) -> None:
        """Start listening for events."""
        ...

    def stop(self) -> None:
        """Stop listening for events."""
        ...


class ResearchEventBus(Protocol):
    """Port for subscribing to Research BC events.

    Learning subscribes to Research events through this port.
    Reserved for future cross-BC integration with Research.
    """

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Research events."""
        ...

    def start(self) -> None:
        """Start listening for events."""
        ...

    def stop(self) -> None:
        """Stop listening for events."""
        ...


class PublicationEventBus(Protocol):
    """Port for subscribing to Publication BC events.

    Learning subscribes to Publication events through this port.
    Reserved for future cross-BC integration with Publication.
    """

    def subscribe(self, handler: Callable) -> None:
        """Subscribe a handler to receive Publication events."""
        ...

    def start(self) -> None:
        """Start listening for events."""
        ...

    def stop(self) -> None:
        """Stop listening for events."""
        ...
