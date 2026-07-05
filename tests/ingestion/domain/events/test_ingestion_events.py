"""Tests for ingestion domain events."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from foundation.events.domain_event import DomainEvent

from ingestion.domain.entities.ids import FeedId, SourceId
from ingestion.domain.events.ingestion_events import (
    RawArticleCollected,
    SourceDisabled,
    SourceEnabled,
)


class TestRawArticleCollected:
    def test_creation(self) -> None:
        feed_id = FeedId.generate()
        batch_id = uuid4()
        now = datetime.now(timezone.utc)
        event = RawArticleCollected(
            feed_id=feed_id,
            batch_id=batch_id,
            count=5,
            collected_at=now,
        )
        assert event.feed_id == feed_id
        assert event.batch_id == batch_id
        assert event.count == 5
        assert event.collected_at == now

    def test_inherits_domain_event(self) -> None:
        event = RawArticleCollected(
            feed_id=FeedId.generate(),
            batch_id=uuid4(),
            count=3,
            collected_at=datetime.now(timezone.utc),
        )
        assert isinstance(event, DomainEvent)
        assert event.event_name == "RawArticleCollected"
        assert isinstance(event.event_id, UUID)
        assert event.event_version == 1

    def test_frozen_immutable(self) -> None:
        event = RawArticleCollected(
            feed_id=FeedId.generate(),
            batch_id=uuid4(),
            count=3,
            collected_at=datetime.now(timezone.utc),
        )
        with pytest.raises(Exception):
            event.count = 10

    def test_zero_count_valid(self) -> None:
        event = RawArticleCollected(
            feed_id=FeedId.generate(),
            batch_id=uuid4(),
            count=0,
            collected_at=datetime.now(timezone.utc),
        )
        assert event.count == 0


class TestSourceEnabled:
    def test_creation(self) -> None:
        source_id = SourceId.generate()
        now = datetime.now(timezone.utc)
        event = SourceEnabled(
            source_id=source_id,
            enabled_at=now,
        )
        assert event.source_id == source_id
        assert event.enabled_at == now

    def test_inherits_domain_event(self) -> None:
        event = SourceEnabled(
            source_id=SourceId.generate(),
            enabled_at=datetime.now(timezone.utc),
        )
        assert isinstance(event, DomainEvent)
        assert event.event_name == "SourceEnabled"

    def test_frozen_immutable(self) -> None:
        event = SourceEnabled(
            source_id=SourceId.generate(),
            enabled_at=datetime.now(timezone.utc),
        )
        with pytest.raises(Exception):
            event.source_id = SourceId.generate()


class TestSourceDisabled:
    def test_creation(self) -> None:
        source_id = SourceId.generate()
        now = datetime.now(timezone.utc)
        event = SourceDisabled(
            source_id=source_id,
            reason="Rate limit exceeded",
            disabled_at=now,
        )
        assert event.source_id == source_id
        assert event.reason == "Rate limit exceeded"
        assert event.disabled_at == now

    def test_inherits_domain_event(self) -> None:
        event = SourceDisabled(
            source_id=SourceId.generate(),
            reason="test",
            disabled_at=datetime.now(timezone.utc),
        )
        assert isinstance(event, DomainEvent)
        assert event.event_name == "SourceDisabled"

    def test_empty_reason_allowed(self) -> None:
        event = SourceDisabled(
            source_id=SourceId.generate(),
            reason="",
            disabled_at=datetime.now(timezone.utc),
        )
        assert event.reason == ""

    def test_frozen_immutable(self) -> None:
        event = SourceDisabled(
            source_id=SourceId.generate(),
            reason="test",
            disabled_at=datetime.now(timezone.utc),
        )
        with pytest.raises(Exception):
            event.reason = "changed"
