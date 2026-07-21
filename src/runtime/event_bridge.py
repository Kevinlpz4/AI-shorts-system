"""
EventBridge — integration event routing between Bounded Contexts.

The EventBridge is a decorator that wraps an existing publisher,
captures events, routes them to handlers, and maintains a bounded buffer.

Pattern: ``EventBridgePublisher(inner, bridge)`` wraps ``inner``,
captures all events, and routes them through ``bridge``.

Usage::

    from runtime.event_bridge import EventBridge, EventBridgePublisher

    bridge = EventBridge(max_buffer=500)
    bridge.subscribe("ingestion.completed", my_handler)

    publisher = EventBridgePublisher(inner=existing_bus, bridge=bridge)
    publisher.publish(IntegrationEvent(event_type="ingestion.completed"))
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class IntegrationEvent:
    """Integration event — crosses BC boundaries.

    Attributes:
        event_type: Type identifier for routing (e.g., ``"ingestion.completed"``).
        payload: Event data as key-value pairs.
        source: Origin of the event (e.g., ``"ingestion"``).
    """

    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""


class EventBridge:
    """Event router with bounded buffer and handler subscription.

    Maintains a deque of events with configurable maxlen. When an event
    is routed, all subscribed handlers for that event type are called.

    Args:
        max_buffer: Maximum number of events to keep in the buffer.
            Oldest events are dropped when the buffer is full.
    """

    def __init__(self, max_buffer: int = 1000) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._buffer: deque[IntegrationEvent] = deque(maxlen=max_buffer)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The event type to listen for.
            handler: Callable that receives the IntegrationEvent.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def route(self, event: IntegrationEvent) -> None:
        """Route an event: buffer it and notify subscribed handlers.

        Args:
            event: The integration event to route.
        """
        self._buffer.append(event)
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def drain(self) -> list[IntegrationEvent]:
        """Return all buffered events and clear the buffer.

        Returns:
            List of all events that were in the buffer.
        """
        events = list(self._buffer)
        self._buffer.clear()
        return events

    def get_pending_count(self) -> int:
        """Return the number of events currently in the buffer."""
        return len(self._buffer)


class EventBridgePublisher:
    """Decorator that wraps a publisher and routes events through EventBridge.

    Captures all published events, delegates to the inner publisher
    (if it has a ``publish`` method), and routes through the bridge.

    Args:
        inner: The original publisher to delegate to (can be None).
        bridge: The EventBridge to route events through.
    """

    def __init__(self, inner: Any, bridge: EventBridge) -> None:
        self._inner = inner
        self._bridge = bridge

    def publish(self, event: IntegrationEvent) -> None:
        """Publish an event — delegate to inner and route through bridge.

        Args:
            event: The integration event to publish.
        """
        if hasattr(self._inner, "publish"):
            self._inner.publish(event)
        self._bridge.route(event)

    def publish_many(self, events: list[IntegrationEvent]) -> None:
        """Publish multiple events sequentially.

        Args:
            events: List of integration events to publish.
        """
        for event in events:
            self.publish(event)
