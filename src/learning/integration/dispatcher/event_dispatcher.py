"""
Event Dispatcher — decoupled, Open/Closed event dispatch.

Register handlers dynamically without modifying existing code.
Multiple handlers per event type. Exceptions are caught per handler.

Usage:
    dispatcher = EventDispatcher()
    dispatcher.register(RawArticleCollected, my_handler)
    errors = dispatcher.dispatch(event)
"""
from __future__ import annotations

from typing import Callable

from foundation.events.integration_event import IntegrationEvent


class EventDispatcher:
    """Decoupled event dispatcher. Open/Closed — register handlers dynamically.

    Handlers are plain callables that receive an IntegrationEvent.
    Multiple handlers can be registered for the same event type.
    Dispatching catches exceptions per handler — one failing handler
    does not prevent others from executing.

    Thread-safe registration (dict operations are atomic in CPython).
    """

    def __init__(self) -> None:
        self._handlers: dict[type[IntegrationEvent], list[Callable]] = {}

    def register(self, event_type: type[IntegrationEvent], handler: Callable) -> None:
        """Register a handler for an event type. Multiple handlers allowed.

        Args:
            event_type: The IntegrationEvent subclass to handle.
            handler: A callable that receives an instance of event_type.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unregister(self, event_type: type[IntegrationEvent], handler: Callable) -> None:
        """Remove a specific handler for an event type.

        Args:
            event_type: The event type the handler was registered for.
            handler: The specific handler to remove.

        Raises:
            KeyError: If the event_type has no registered handlers.
            ValueError: If the handler is not registered for this event type.
        """
        if event_type not in self._handlers:
            raise KeyError(f"No handlers registered for {event_type.__name__}")
        self._handlers[event_type].remove(handler)

    def dispatch(self, event: IntegrationEvent) -> list[Exception]:
        """Dispatch event to all registered handlers. Returns list of errors.

        Catches exceptions per handler — does not stop on first error.
        Handlers are called in registration order.

        Args:
            event: The IntegrationEvent instance to dispatch.

        Returns:
            List of exceptions (empty = all handlers succeeded).
        """
        errors: list[Exception] = []
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                errors.append(e)

        return errors

    def has_handlers(self, event_type: type[IntegrationEvent]) -> bool:
        """Check if any handlers are registered for an event type.

        Args:
            event_type: The event type to check.

        Returns:
            True if at least one handler is registered.
        """
        return len(self._handlers.get(event_type, [])) > 0

    def handler_count(self, event_type: type[IntegrationEvent]) -> int:
        """Return number of handlers registered for an event type.

        Args:
            event_type: The event type to count handlers for.

        Returns:
            Number of registered handlers.
        """
        return len(self._handlers.get(event_type, []))
