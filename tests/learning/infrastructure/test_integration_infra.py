"""
Tests for InMemory Integration infrastructure — event buses, read models, and cross-BC adapters.

Covers:
- InMemoryIntegrationEventBus: publish, publish_many, clear
- InMemoryIngestionEventBus: subscribe, unsubscribe, start/stop, dispatch
- InMemoryArticleReadModel: get, not found, by source
- InMemoryIngestionReader: get_article_features, get_source_config, not found
"""
from __future__ import annotations

import pytest

from foundation.events.integration_event import IntegrationEvent
from foundation.result.result import Error, ErrorCode, Result

from learning.infrastructure.inmemory.integration.event_buses import (
    InMemoryIngestionEventBus,
    InMemoryIntegrationEventBus,
)
from learning.infrastructure.inmemory.integration.read_models import (
    InMemoryArticleReadModel,
)
from learning.infrastructure.inmemory.cross_bc_adapters import (
    InMemoryIngestionReader,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(*, source_boundary: str = "learning") -> IntegrationEvent:
    """Create a test IntegrationEvent."""
    return IntegrationEvent(source_boundary=source_boundary)


# ===========================================================================
# InMemoryIntegrationEventBus
# ===========================================================================


class TestInMemoryIntegrationEventBus:
    """Tests for the outbound integration event bus."""

    def test_publish(self) -> None:
        """publish stores a single event."""
        bus = InMemoryIntegrationEventBus()
        event = _make_event()

        bus.publish(event)

        assert len(bus.published_events) == 1
        assert bus.published_events[0] is event

    def test_publish_many(self) -> None:
        """publish_many stores multiple events atomically."""
        bus = InMemoryIntegrationEventBus()
        events = [_make_event() for i in range(3)]

        bus.publish_many(events)

        assert len(bus.published_events) == 3
        assert bus.published_events == events

    def test_clear(self) -> None:
        """clear removes all accumulated events."""
        bus = InMemoryIntegrationEventBus()
        bus.publish(_make_event())
        bus.publish(_make_event())

        bus.clear()

        assert len(bus.published_events) == 0

    def test_published_events_returns_copy(self) -> None:
        """published_events returns a copy — external mutation is safe."""
        bus = InMemoryIntegrationEventBus()
        bus.publish(_make_event())

        events = bus.published_events
        events.clear()

        # Original is unaffected
        assert len(bus.published_events) == 1


# ===========================================================================
# InMemoryIngestionEventBus
# ===========================================================================


class TestInMemoryIngestionEventBus:
    """Tests for the inbound Ingestion event bus."""

    def test_subscribe(self) -> None:
        """subscribe registers a handler."""
        bus = InMemoryIngestionEventBus()
        handler = lambda e: None

        bus.subscribe(handler)

        assert bus.handler_count == 1

    def test_unsubscribe(self) -> None:
        """unsubscribe removes a previously registered handler."""
        bus = InMemoryIngestionEventBus()
        handler = lambda e: None

        bus.subscribe(handler)
        assert bus.handler_count == 1

        bus.unsubscribe(handler)
        assert bus.handler_count == 0

    def test_unsubscribe_not_registered_raises(self) -> None:
        """unsubscribe raises ValueError for an unregistered handler."""
        bus = InMemoryIngestionEventBus()
        handler = lambda e: None

        with pytest.raises(ValueError):
            bus.unsubscribe(handler)

    def test_start_stop(self) -> None:
        """start/stop toggle the is_running flag."""
        bus = InMemoryIngestionEventBus()

        assert bus.is_running is False

        bus.start()
        assert bus.is_running is True

        bus.stop()
        assert bus.is_running is False

    def test_publish_dispatches_to_handlers(self) -> None:
        """publish dispatches the event to all subscribed handlers."""
        bus = InMemoryIngestionEventBus()
        received: list[IntegrationEvent] = []
        handler = lambda e: received.append(e)

        bus.subscribe(handler)
        event = _make_event()
        bus.publish(event)

        assert len(received) == 1
        assert received[0] is event

    def test_publish_multiple_handlers(self) -> None:
        """publish dispatches to all subscribed handlers."""
        bus = InMemoryIngestionEventBus()
        received_a: list[IntegrationEvent] = []
        received_b: list[IntegrationEvent] = []

        bus.subscribe(lambda e: received_a.append(e))
        bus.subscribe(lambda e: received_b.append(e))

        event = _make_event()
        bus.publish(event)

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_publish_no_handlers(self) -> None:
        """publish with no handlers does not raise."""
        bus = InMemoryIngestionEventBus()
        event = _make_event()
        bus.publish(event)  # Should not raise

    def test_publish_records_events_received(self) -> None:
        """publish stores events in _events_received for inspection."""
        bus = InMemoryIngestionEventBus()
        event = _make_event()
        bus.publish(event)

        # Access internal list via publish property (test helper)
        assert len(bus._events_received) == 1
        assert bus._events_received[0] is event


# ===========================================================================
# InMemoryArticleReadModel
# ===========================================================================


class TestInMemoryArticleReadModel:
    """Tests for the InMemory article read model."""

    def test_get_article(self) -> None:
        """get_article returns the article dict for a valid ID."""
        articles = {
            "a1": {"id": "a1", "source_name": "reuters", "title": "Test Article"},
        }
        model = InMemoryArticleReadModel(articles=articles)

        result = model.get_article("a1")

        assert result.is_success
        assert result.unwrap()["title"] == "Test Article"

    def test_get_article_not_found(self) -> None:
        """get_article returns Failure for a non-existent article ID."""
        model = InMemoryArticleReadModel()

        result = model.get_article("nonexistent")

        assert result.is_failure
        assert "not found" in result.error.message

    def test_get_articles_by_source(self) -> None:
        """get_articles_by_source returns articles filtered by source name."""
        articles = {
            "a1": {"id": "a1", "source_name": "reuters", "title": "Article 1"},
            "a2": {"id": "a2", "source_name": "reuters", "title": "Article 2"},
            "a3": {"id": "a3", "source_name": "bbc", "title": "Article 3"},
        }
        model = InMemoryArticleReadModel(articles=articles)

        result = model.get_articles_by_source("reuters")

        assert result.is_success
        articles_list = result.unwrap()
        assert len(articles_list) == 2
        assert all(a["source_name"] == "reuters" for a in articles_list)

    def test_get_articles_by_source_with_limit(self) -> None:
        """get_articles_by_source respects the limit parameter."""
        articles = {
            f"a{i}": {"id": f"a{i}", "source_name": "reuters", "title": f"Article {i}"}
            for i in range(5)
        }
        model = InMemoryArticleReadModel(articles=articles)

        result = model.get_articles_by_source("reuters", limit=2)

        assert result.is_success
        assert len(result.unwrap()) == 2

    def test_get_articles_by_source_empty(self) -> None:
        """get_articles_by_source returns empty list when no articles match."""
        model = InMemoryArticleReadModel()

        result = model.get_articles_by_source("reuters")

        assert result.is_success
        assert result.unwrap() == []


# ===========================================================================
# InMemoryIngestionReader
# ===========================================================================


class TestInMemoryIngestionReader:
    """Tests for the InMemory cross-BC Ingestion reader."""

    def test_get_article_features(self) -> None:
        """get_article_features returns article data for a valid ID."""
        articles = {"a1": {"title": "AI News", "keywords": ["ai", "llm"]}}
        reader = InMemoryIngestionReader(articles=articles)

        result = reader.get_article_features("a1")

        assert result.is_success
        assert result.unwrap()["keywords"] == ["ai", "llm"]

    def test_get_article_features_not_found(self) -> None:
        """get_article_features returns Failure for a non-existent article."""
        reader = InMemoryIngestionReader()

        result = reader.get_article_features("nonexistent")

        assert result.is_failure
        assert "not found" in result.error.message

    def test_get_source_config(self) -> None:
        """get_source_config returns source data for a valid name."""
        sources = {"reuters": {"name": "reuters", "quality": 0.9}}
        reader = InMemoryIngestionReader(sources=sources)

        result = reader.get_source_config("reuters")

        assert result.is_success
        assert result.unwrap()["quality"] == 0.9

    def test_get_source_config_not_found(self) -> None:
        """get_source_config returns Failure for a non-existent source."""
        reader = InMemoryIngestionReader()

        result = reader.get_source_config("nonexistent")

        assert result.is_failure
        assert "not found" in result.error.message

    def test_empty_constructor(self) -> None:
        """InMemoryIngestionReader with no args returns failures for all queries."""
        reader = InMemoryIngestionReader()

        assert reader.get_article_features("a1").is_failure
        assert reader.get_source_config("s1").is_failure
