"""
Tests for EventBridge — route, buffer bounds, drain, subscribe.

Covers:
- Subscribe and route events
- Buffer maxlen enforcement
- Drain returns and clears buffer
- Multiple handlers for same event type
- No handler for unknown event type
- Pending count
"""
from __future__ import annotations


from runtime.event_bridge import EventBridge, EventBridgePublisher, RoutingEvent


class TestEventBridge:
    """Tests for EventBridge."""

    def test_route_event_to_subscriber(self) -> None:
        """Routed events reach subscribed handlers."""
        bridge = EventBridge()
        received: list[RoutingEvent] = []

        bridge.subscribe("test.event", lambda e: received.append(e))

        event = RoutingEvent(event_type="test.event", payload={"key": "val"})
        bridge.route(event)

        assert len(received) == 1
        assert received[0] is event

    def test_route_without_handler(self) -> None:
        """Routing an event with no handler does not raise."""
        bridge = EventBridge()
        event = RoutingEvent(event_type="unknown")

        # Should not raise
        bridge.route(event)
        assert bridge.get_pending_count() == 1

    def test_multiple_handlers(self) -> None:
        """Multiple handlers for same event type all receive the event."""
        bridge = EventBridge()
        received_a: list[RoutingEvent] = []
        received_b: list[RoutingEvent] = []

        bridge.subscribe("test.event", lambda e: received_a.append(e))
        bridge.subscribe("test.event", lambda e: received_b.append(e))

        event = RoutingEvent(event_type="test.event")
        bridge.route(event)

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_buffer_maxlen(self) -> None:
        """Buffer enforces maxlen — oldest events are dropped."""
        bridge = EventBridge(max_buffer=3)

        for i in range(5):
            bridge.route(RoutingEvent(event_type="e", payload={"i": str(i)}))

        assert bridge.get_pending_count() == 3
        # First two should have been dropped
        events = bridge.drain()
        assert events[0].payload == {"i": "2"}
        assert events[1].payload == {"i": "3"}
        assert events[2].payload == {"i": "4"}

    def test_drain_returns_and_clears(self) -> None:
        """drain returns all buffered events and clears the buffer."""
        bridge = EventBridge()
        e1 = RoutingEvent(event_type="a")
        e2 = RoutingEvent(event_type="b")

        bridge.route(e1)
        bridge.route(e2)

        drained = bridge.drain()

        assert len(drained) == 2
        assert drained[0] is e1
        assert drained[1] is e2
        assert bridge.get_pending_count() == 0

    def test_drain_empty_buffer(self) -> None:
        """drain on empty buffer returns empty list."""
        bridge = EventBridge()

        assert bridge.drain() == []

    def test_get_pending_count(self) -> None:
        """get_pending_count returns number of buffered events."""
        bridge = EventBridge()

        assert bridge.get_pending_count() == 0

        bridge.route(RoutingEvent(event_type="a"))
        assert bridge.get_pending_count() == 1

        bridge.route(RoutingEvent(event_type="b"))
        assert bridge.get_pending_count() == 2

    def test_different_event_types(self) -> None:
        """Handlers only receive events matching their subscribed type."""
        bridge = EventBridge()
        type_a: list[RoutingEvent] = []
        type_b: list[RoutingEvent] = []

        bridge.subscribe("type_a", lambda e: type_a.append(e))
        bridge.subscribe("type_b", lambda e: type_b.append(e))

        bridge.route(RoutingEvent(event_type="type_a"))
        bridge.route(RoutingEvent(event_type="type_b"))
        bridge.route(RoutingEvent(event_type="type_a"))

        assert len(type_a) == 2
        assert len(type_b) == 1

    def test_event_stored_in_buffer(self) -> None:
        """Routed events are stored in the buffer."""
        bridge = EventBridge()
        event = RoutingEvent(event_type="test", payload={"x": "y"})

        bridge.route(event)

        events = bridge.drain()
        assert events[0] is event

    def test_default_buffer_size(self) -> None:
        """Default buffer size is 1000."""
        bridge = EventBridge()
        # Just verify it doesn't crash with many events
        for i in range(100):
            bridge.route(RoutingEvent(event_type="e"))
        assert bridge.get_pending_count() == 100


class TestEventBridgePublisher:
    """Tests for EventBridgePublisher decorator."""

    def test_publish_routes_to_bridge(self) -> None:
        """publish routes events through the bridge."""
        bridge = EventBridge()
        publisher = EventBridgePublisher(inner=None, bridge=bridge)

        event = RoutingEvent(event_type="test")
        publisher.publish(event)

        assert bridge.get_pending_count() == 1

    def test_publish_delegates_to_inner(self) -> None:
        """publish calls inner.publish if available."""
        received: list[RoutingEvent] = []

        class FakeInner:
            def publish(self, event: RoutingEvent) -> None:
                received.append(event)

        bridge = EventBridge()
        publisher = EventBridgePublisher(inner=FakeInner(), bridge=bridge)

        event = RoutingEvent(event_type="test")
        publisher.publish(event)

        assert len(received) == 1
        assert received[0] is event

    def test_publish_many(self) -> None:
        """publish_many routes multiple events through bridge."""
        bridge = EventBridge()
        publisher = EventBridgePublisher(inner=None, bridge=bridge)

        events = [
            RoutingEvent(event_type="a"),
            RoutingEvent(event_type="b"),
            RoutingEvent(event_type="c"),
        ]
        publisher.publish_many(events)

        assert bridge.get_pending_count() == 3

    def test_inner_without_publish(self) -> None:
        """publish works when inner has no publish method."""
        bridge = EventBridge()
        publisher = EventBridgePublisher(inner="not a publisher", bridge=bridge)

        event = RoutingEvent(event_type="test")
        publisher.publish(event)

        assert bridge.get_pending_count() == 1

    def test_capture_pattern(self) -> None:
        """EventBridgePublisher wraps, delegates, and captures events."""
        captured: list[RoutingEvent] = []

        class FakeBus:
            def publish(self, event: RoutingEvent) -> None:
                captured.append(event)

        bridge = EventBridge()
        publisher = EventBridgePublisher(inner=FakeBus(), bridge=bridge)

        event = RoutingEvent(event_type="integration.test")
        publisher.publish(event)

        # Captured by inner bus
        assert len(captured) == 1
        # Also routed through bridge
        assert bridge.get_pending_count() == 1
