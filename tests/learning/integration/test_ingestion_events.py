"""
Tests for Ingestion Events — 5 inbound Integration Events from Ingestion BC.

Validates: frozen dataclasses, IntegrationEvent inheritance, source_boundary defaults,
event_name property, construction with all fields, and equality semantics.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from foundation.events.integration_event import IntegrationEvent

FIXED_TS = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
from learning.integration.events.ingestion_events import (
    ArticleCreated,
    FeedRegistered,
    RawArticleCollected,
    RawArticleRejected,
    SourceRegistered,
)


# ─── RawArticleCollected ──────────────────────────────────────────────

class TestRawArticleCollected:
    """RawArticleCollected — Ingestion collected a new raw article."""

    def _make(self) -> RawArticleCollected:
        return RawArticleCollected(
            article_id="art-001",
            source_name="Reuters",
            title="Breaking News",
            url="https://example.com/article",
            collected_at="2026-07-15T10:00:00Z",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "ingestion"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "RawArticleCollected"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.article_id == "art-001"
        assert event.source_name == "Reuters"
        assert event.title == "Breaking News"
        assert event.url == "https://example.com/article"
        assert event.collected_at == "2026-07-15T10:00:00Z"

    def test_construction_defaults(self) -> None:
        event = RawArticleCollected()
        assert event.article_id == ""
        assert event.source_name == ""
        assert event.title == ""
        assert event.url == ""
        assert event.collected_at == ""
        assert event.source_boundary == "ingestion"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.article_id = "changed"  # type: ignore[misc]

    def test_frozen_source_boundary(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.source_boundary = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = RawArticleCollected(event_id=eid, occurred_at=FIXED_TS, article_id="art-001", source_name="Reuters")
        b = RawArticleCollected(event_id=eid, occurred_at=FIXED_TS, article_id="art-001", source_name="Reuters")
        assert a == b

    def test_inequality_different_id(self) -> None:
        a = RawArticleCollected(article_id="art-001")
        b = RawArticleCollected(article_id="art-001")
        assert a != b  # Different event_id

    def test_inequality_different_data(self) -> None:
        eid = uuid4()
        a = RawArticleCollected(event_id=eid, article_id="art-001")
        b = RawArticleCollected(event_id=eid, article_id="art-002")
        assert a != b

    def test_has_event_id(self) -> None:
        event = self._make()
        assert isinstance(event.event_id, type(uuid4()))

    def test_has_occurred_at(self) -> None:
        event = self._make()
        assert event.occurred_at is not None


# ─── RawArticleRejected ───────────────────────────────────────────────

class TestRawArticleRejected:
    """RawArticleRejected — Ingestion rejected a raw article."""

    def _make(self) -> RawArticleRejected:
        return RawArticleRejected(
            article_id="art-002",
            source_name="SpamBlog",
            reason="Duplicate content",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "ingestion"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "RawArticleRejected"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.article_id == "art-002"
        assert event.source_name == "SpamBlog"
        assert event.reason == "Duplicate content"

    def test_construction_defaults(self) -> None:
        event = RawArticleRejected()
        assert event.article_id == ""
        assert event.source_name == ""
        assert event.reason == ""
        assert event.source_boundary == "ingestion"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.reason = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = RawArticleRejected(event_id=eid, occurred_at=FIXED_TS, article_id="art-002", reason="spam")
        b = RawArticleRejected(event_id=eid, occurred_at=FIXED_TS, article_id="art-002", reason="spam")
        assert a == b

    def test_inequality(self) -> None:
        a = RawArticleRejected(article_id="art-002")
        b = RawArticleRejected(article_id="art-003")
        assert a != b


# ─── SourceRegistered ─────────────────────────────────────────────────

class TestSourceRegistered:
    """SourceRegistered — A new source was registered in Ingestion."""

    def _make(self) -> SourceRegistered:
        return SourceRegistered(
            source_id="src-001",
            source_name="Reuters",
            source_type="rss",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "ingestion"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "SourceRegistered"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.source_id == "src-001"
        assert event.source_name == "Reuters"
        assert event.source_type == "rss"

    def test_construction_defaults(self) -> None:
        event = SourceRegistered()
        assert event.source_id == ""
        assert event.source_name == ""
        assert event.source_type == ""
        assert event.source_boundary == "ingestion"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.source_name = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = SourceRegistered(event_id=eid, occurred_at=FIXED_TS, source_id="src-001", source_name="Reuters")
        b = SourceRegistered(event_id=eid, occurred_at=FIXED_TS, source_id="src-001", source_name="Reuters")
        assert a == b

    def test_inequality(self) -> None:
        a = SourceRegistered(source_id="src-001")
        b = SourceRegistered(source_id="src-002")
        assert a != b


# ─── FeedRegistered ───────────────────────────────────────────────────

class TestFeedRegistered:
    """FeedRegistered — A new feed was registered in Ingestion."""

    def _make(self) -> FeedRegistered:
        return FeedRegistered(
            feed_id="feed-001",
            source_id="src-001",
            feed_url="https://feeds.example.com/rss",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "ingestion"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "FeedRegistered"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.feed_id == "feed-001"
        assert event.source_id == "src-001"
        assert event.feed_url == "https://feeds.example.com/rss"

    def test_construction_defaults(self) -> None:
        event = FeedRegistered()
        assert event.feed_id == ""
        assert event.source_id == ""
        assert event.feed_url == ""
        assert event.source_boundary == "ingestion"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.feed_url = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = FeedRegistered(event_id=eid, occurred_at=FIXED_TS, feed_id="feed-001", source_id="src-001")
        b = FeedRegistered(event_id=eid, occurred_at=FIXED_TS, feed_id="feed-001", source_id="src-001")
        assert a == b

    def test_inequality(self) -> None:
        a = FeedRegistered(feed_id="feed-001")
        b = FeedRegistered(feed_id="feed-002")
        assert a != b


# ─── ArticleCreated ───────────────────────────────────────────────────

class TestArticleCreated:
    """ArticleCreated — A processed article was created."""

    def _make(self) -> ArticleCreated:
        return ArticleCreated(
            article_id="art-010",
            source_name="Reuters",
            title="AI Breakthrough",
            content_preview="Scientists have discovered...",
        )

    def test_inherits_integration_event(self) -> None:
        event = self._make()
        assert isinstance(event, IntegrationEvent)

    def test_source_boundary_default(self) -> None:
        event = self._make()
        assert event.source_boundary == "ingestion"

    def test_event_name_property(self) -> None:
        event = self._make()
        assert event.event_name == "ArticleCreated"

    def test_construction_all_fields(self) -> None:
        event = self._make()
        assert event.article_id == "art-010"
        assert event.source_name == "Reuters"
        assert event.title == "AI Breakthrough"
        assert event.content_preview == "Scientists have discovered..."

    def test_construction_defaults(self) -> None:
        event = ArticleCreated()
        assert event.article_id == ""
        assert event.source_name == ""
        assert event.title == ""
        assert event.content_preview == ""
        assert event.source_boundary == "ingestion"

    def test_frozen(self) -> None:
        event = self._make()
        with pytest.raises(AttributeError):
            event.title = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        eid = uuid4()
        a = ArticleCreated(event_id=eid, occurred_at=FIXED_TS, article_id="art-010", title="Test")
        b = ArticleCreated(event_id=eid, occurred_at=FIXED_TS, article_id="art-010", title="Test")
        assert a == b

    def test_inequality(self) -> None:
        a = ArticleCreated(article_id="art-010")
        b = ArticleCreated(article_id="art-011")
        assert a != b
