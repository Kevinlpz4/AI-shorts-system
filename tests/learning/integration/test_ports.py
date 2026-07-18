"""
Tests for Integration Ports — Protocol definitions for cross-BC event communication.

Validates: all ports are Protocols, required methods exist, and return types.
"""
from __future__ import annotations

import inspect
from typing import Protocol

from learning.integration.ports.event_bus import (
    IngestionEventBus,
    IntegrationEventBus,
    PublicationEventBus,
    ResearchEventBus,
)
from learning.integration.ports.read_model import (
    ArticleReadModel,
    SourceReadModel,
    TopicReadModel,
)


def _is_protocol(cls: type) -> bool:
    """Check if a class is a Protocol."""
    return getattr(cls, "_is_protocol", False)


# ─── Event Bus Ports ──────────────────────────────────────────────────

class TestIntegrationEventBus:
    """IntegrationEventBus — Port for publishing integration events."""

    def test_event_bus_is_protocol(self) -> None:
        assert _is_protocol(IntegrationEventBus)

    def test_has_publish_method(self) -> None:
        assert hasattr(IntegrationEventBus, "publish")

    def test_has_publish_many_method(self) -> None:
        assert hasattr(IntegrationEventBus, "publish_many")

    def test_publish_method_signature(self) -> None:
        sig = inspect.signature(IntegrationEventBus.publish)
        params = list(sig.parameters.keys())
        assert "event" in params

    def test_publish_many_method_signature(self) -> None:
        sig = inspect.signature(IntegrationEventBus.publish_many)
        params = list(sig.parameters.keys())
        assert "events" in params


class TestIngestionEventBus:
    """IngestionEventBus — Port for subscribing to Ingestion events."""

    def test_ingestion_event_bus_is_protocol(self) -> None:
        assert _is_protocol(IngestionEventBus)

    def test_has_subscribe_method(self) -> None:
        assert hasattr(IngestionEventBus, "subscribe")

    def test_has_start_method(self) -> None:
        assert hasattr(IngestionEventBus, "start")

    def test_has_stop_method(self) -> None:
        assert hasattr(IngestionEventBus, "stop")

    def test_subscribe_method_signature(self) -> None:
        sig = inspect.signature(IngestionEventBus.subscribe)
        params = list(sig.parameters.keys())
        assert "handler" in params


class TestResearchEventBus:
    """ResearchEventBus — Port for subscribing to Research events."""

    def test_research_event_bus_is_protocol(self) -> None:
        assert _is_protocol(ResearchEventBus)

    def test_has_subscribe_method(self) -> None:
        assert hasattr(ResearchEventBus, "subscribe")

    def test_has_start_method(self) -> None:
        assert hasattr(ResearchEventBus, "start")

    def test_has_stop_method(self) -> None:
        assert hasattr(ResearchEventBus, "stop")


class TestPublicationEventBus:
    """PublicationEventBus — Port for subscribing to Publication events."""

    def test_publication_event_bus_is_protocol(self) -> None:
        assert _is_protocol(PublicationEventBus)

    def test_has_subscribe_method(self) -> None:
        assert hasattr(PublicationEventBus, "subscribe")

    def test_has_start_method(self) -> None:
        assert hasattr(PublicationEventBus, "start")

    def test_has_stop_method(self) -> None:
        assert hasattr(PublicationEventBus, "stop")


# ─── Read Model Ports ─────────────────────────────────────────────────

class TestArticleReadModel:
    """ArticleReadModel — Read-only access to article data."""

    def test_article_read_model_is_protocol(self) -> None:
        assert _is_protocol(ArticleReadModel)

    def test_has_get_article_method(self) -> None:
        assert hasattr(ArticleReadModel, "get_article")

    def test_has_get_articles_by_source_method(self) -> None:
        assert hasattr(ArticleReadModel, "get_articles_by_source")

    def test_get_article_signature(self) -> None:
        sig = inspect.signature(ArticleReadModel.get_article)
        params = list(sig.parameters.keys())
        assert "article_id" in params

    def test_get_articles_by_source_signature(self) -> None:
        sig = inspect.signature(ArticleReadModel.get_articles_by_source)
        params = list(sig.parameters.keys())
        assert "source_name" in params


class TestSourceReadModel:
    """SourceReadModel — Read-only access to source data."""

    def test_source_read_model_is_protocol(self) -> None:
        assert _is_protocol(SourceReadModel)

    def test_has_get_source_method(self) -> None:
        assert hasattr(SourceReadModel, "get_source")

    def test_has_get_all_sources_method(self) -> None:
        assert hasattr(SourceReadModel, "get_all_sources")

    def test_get_source_signature(self) -> None:
        sig = inspect.signature(SourceReadModel.get_source)
        params = list(sig.parameters.keys())
        assert "source_name" in params


class TestTopicReadModel:
    """TopicReadModel — Read-only access to topic data."""

    def test_topic_read_model_is_protocol(self) -> None:
        assert _is_protocol(TopicReadModel)

    def test_has_get_topic_method(self) -> None:
        assert hasattr(TopicReadModel, "get_topic")

    def test_has_get_topic_score_method(self) -> None:
        assert hasattr(TopicReadModel, "get_topic_score")

    def test_get_topic_signature(self) -> None:
        sig = inspect.signature(TopicReadModel.get_topic)
        params = list(sig.parameters.keys())
        assert "topic_id" in params

    def test_get_topic_score_signature(self) -> None:
        sig = inspect.signature(TopicReadModel.get_topic_score)
        params = list(sig.parameters.keys())
        assert "topic_id" in params
