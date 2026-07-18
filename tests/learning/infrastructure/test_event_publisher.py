"""
Tests for InMemoryLearningEventPublisher (generic event publisher).

Covers publish, publish_many, has_event, published_events, and clear.
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.events.domain_event import DomainEvent
from learning.infrastructure.inmemory.event_publisher import (
    InMemoryLearningEventPublisher,
)


# ---------------------------------------------------------------------------
# Fake event types for testing (avoid coupling to real domain events)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FakeEventA(DomainEvent):
    name: str = "event_a"


@dataclass(frozen=True)
class FakeEventB(DomainEvent):
    name: str = "event_b"


class TestInMemoryLearningEventPublisher:
    """Tests for the generic InMemoryLearningEventPublisher."""

    def test_publish_single(self) -> None:
        publisher = InMemoryLearningEventPublisher()
        event = FakeEventA(name="first")

        publisher.publish(event)

        assert len(publisher.published_events) == 1
        assert publisher.published_events[0] is event

    def test_publish_many(self) -> None:
        publisher = InMemoryLearningEventPublisher()
        events = [FakeEventA(name=f"ev-{i}") for i in range(3)]

        publisher.publish_many(events)

        assert len(publisher.published_events) == 3
        assert publisher.published_events == events

    def test_has_event_true(self) -> None:
        publisher = InMemoryLearningEventPublisher()
        publisher.publish(FakeEventA(name="found"))

        assert publisher.has_event(FakeEventA) is True

    def test_has_event_false(self) -> None:
        publisher = InMemoryLearningEventPublisher()
        publisher.publish(FakeEventA(name="only_a"))

        assert publisher.has_event(FakeEventB) is False

    def test_clear(self) -> None:
        publisher = InMemoryLearningEventPublisher()
        publisher.publish(FakeEventA(name="a"))
        publisher.publish(FakeEventB(name="b"))

        publisher.clear()

        assert len(publisher.published_events) == 0
        assert publisher.has_event(FakeEventA) is False
        assert publisher.has_event(FakeEventB) is False

    def test_published_events_returns_copy(self) -> None:
        """published_events returns a new list each call, not the internal one."""
        publisher = InMemoryLearningEventPublisher()
        publisher.publish(FakeEventA(name="x"))

        events1 = publisher.published_events
        events2 = publisher.published_events

        assert events1 is not events2
        assert events1 == events2
