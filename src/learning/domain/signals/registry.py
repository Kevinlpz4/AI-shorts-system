"""
Signal Type Registry — Maps SignalType to SignalHandler.

The registry enables Open/Closed extensibility: new signal types are added
by registering a new handler, without modifying existing code.
"""
from __future__ import annotations

from learning.domain.signals.handlers import (
    CategorySignalHandler,
    KeywordSignalHandler,
    SignalHandler,
    SourceSignalHandler,
    TimeSignalHandler,
    TopicSignalHandler,
)
from learning.domain.value_objects.signal_type import SignalType


class SignalRegistry:
    """Registry mapping SignalType to SignalHandler implementations.

    Usage::

        registry = SignalRegistry()
        # All default handlers are registered automatically
        handler = registry.get_handler(SignalType.KEYWORD)
        strength = handler.compute(data)

        # Extend with a new signal type (without modifying existing code):
        registry.register(MyCustomHandler())
    """

    def __init__(self) -> None:
        """Initialize with all default signal handlers."""
        self._handlers: dict[SignalType, SignalHandler] = {}
        # Register all built-in handlers
        self.register(KeywordSignalHandler())
        self.register(SourceSignalHandler())
        self.register(CategorySignalHandler())
        self.register(TopicSignalHandler())
        self.register(TimeSignalHandler())

    def register(self, handler: SignalHandler) -> None:
        """Register a signal handler for its signal type.

        If a handler for this type already exists, it is replaced.

        Args:
            handler: The handler to register.
        """
        self._handlers[handler.signal_type] = handler

    def get_handler(self, signal_type: SignalType) -> SignalHandler:
        """Get the handler for a given signal type.

        Args:
            signal_type: The signal type to look up.

        Returns:
            The registered handler.

        Raises:
            KeyError: If no handler is registered for this type.
        """
        if signal_type not in self._handlers:
            raise KeyError(
                f"No handler registered for signal type '{signal_type.value}'"
            )
        return self._handlers[signal_type]

    def has_handler(self, signal_type: SignalType) -> bool:
        """Check if a handler is registered for the given signal type."""
        return signal_type in self._handlers

    @property
    def registered_types(self) -> list[SignalType]:
        """List of all registered signal types."""
        return list(self._handlers.keys())

    def __len__(self) -> int:
        return len(self._handlers)

    def __contains__(self, signal_type: SignalType) -> bool:
        return signal_type in self._handlers
