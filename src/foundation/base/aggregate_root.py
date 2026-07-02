"""
AggregateRoot — Base class for Domain Aggregate Roots.

AggregateRoot extends Entity with transient DomainEvent storage:
    - ``register_event(event: DomainEvent)`` accumulates an event internally
    - ``pull_events()`` returns a DEFENSIVE COPY of all events and clears
      the internal collection

Constraints:
    - ``_events`` is ``list[DomainEvent]`` (narrowed from ``list[Any]``
      in Sprint 2.4). AggregateRoot only stores DomainEvent instances.
    - AggregateRoot ONLY stores events. It does NOT publish, dispatch,
      commit, or know about any infrastructure. The Application Service
      is responsible for persisting the aggregate and publishing events
      after ``pull_events()``.

Defensive copy:
    ``pull_events()`` creates a NEW list via ``list(self._events)`` before
    clearing the internal collection. This ensures that the caller cannot
    mutate the aggregate's internal state.
"""

from dataclasses import dataclass, field

from foundation.base.entity import Entity
from foundation.events.domain_event import DomainEvent


@dataclass(eq=False)
class AggregateRoot(Entity):
    """
    Base class for all Aggregate Roots in the system.

    Extends Entity with:
        - Transient internal DomainEvent storage
        - register_event(event: DomainEvent) — accumulates events
        - pull_events() — extracts events with defensive copy, clears storage

    AggregateRoot only stores events. It does NOT know about:
        - Event publishing or dispatching
        - Infrastructure concerns (commit, flush, etc.)
        - Application services
    """
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    def register_event(self, event: DomainEvent) -> None:
        """
        Register a domain event for later retrieval.

        The event is stored internally. No publishing, dispatching, or
        infrastructure logic runs here — AggregateRoot only stores events.

        Args:
            event: The DomainEvent to store.

        Raises:
            TypeError: If event is not a DomainEvent instance.
        """
        if not isinstance(event, DomainEvent):
            raise TypeError(
                f"AggregateRoot.register_event() requires a DomainEvent, "
                f"got {type(event).__name__}"
            )
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """
        Extract all accumulated events and clear the internal collection.

        Creates a DEFENSIVE COPY before clearing, so the caller cannot
        mutate the aggregate's internal state.

        Returns:
            A new list containing all accumulated DomainEvents (empty list if none).

        Usage:
            events = aggregate.pull_events()
            # Application Service: persist aggregate, then publish events
        """
        events = list(self._events)
        self._events.clear()
        return events
