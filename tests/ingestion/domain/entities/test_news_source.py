"""
Tests for NewsSource aggregate root.

Covers:
  - Construction (valid/invalid)
  - Invariants (I-01 to I-04)
  - Behavior (enable, disable, change_url, assign/remove category/topic)
  - Domain events (SourceEnabled, SourceDisabled)
  - Equality and hash
"""

from __future__ import annotations

import pytest

from foundation.base.aggregate_root import AggregateRoot
from foundation.base.entity import Entity

from ingestion.domain.entities.ids import CategoryId, SourceId, TopicId
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.events.ingestion_events import SourceDisabled, SourceEnabled
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl


class TestNewsSourceCreation:
    def test_create_valid_source(self, source_id: SourceId, valid_source_url: SourceUrl) -> None:
        source = NewsSource(
            id=source_id,
            name="Reddit",
            source_type=SourceType.SOCIAL_MEDIA,
            source_url=valid_source_url,
        )
        assert source.id == source_id
        assert source.name == "Reddit"
        assert source.source_type == SourceType.SOCIAL_MEDIA
        assert source.source_url == valid_source_url
        assert source.is_active is True
        assert source.categories == []
        assert source.topics == []

    def test_empty_name_raises(self, source_id: SourceId, valid_source_url: SourceUrl) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            NewsSource(
                id=source_id,
                name="",
                source_type=SourceType.RSS,
                source_url=valid_source_url,
            )

    def test_whitespace_name_raises(self, source_id: SourceId, valid_source_url: SourceUrl) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            NewsSource(
                id=source_id,
                name="   ",
                source_type=SourceType.RSS,
                source_url=valid_source_url,
            )

    def test_inherits_aggregate_root(self, news_source: NewsSource) -> None:
        assert isinstance(news_source, AggregateRoot)
        assert isinstance(news_source, Entity)

    def test_equality_by_id(self, source_id: SourceId, valid_source_url: SourceUrl) -> None:
        source1 = NewsSource(
            id=source_id,
            name="Reddit",
            source_type=SourceType.SOCIAL_MEDIA,
            source_url=valid_source_url,
        )
        source2 = NewsSource(
            id=source_id,
            name="Reddit Copy",
            source_type=SourceType.RSS,
            source_url=valid_source_url,
        )
        assert source1 == source2

    def test_inequality(self, source_id: SourceId, valid_source_url: SourceUrl) -> None:
        source1 = NewsSource(
            id=source_id,
            name="Reddit",
            source_type=SourceType.SOCIAL_MEDIA,
            source_url=valid_source_url,
        )
        source2 = NewsSource(
            id=SourceId.generate(),
            name="Reddit",
            source_type=SourceType.SOCIAL_MEDIA,
            source_url=valid_source_url,
        )
        assert source1 != source2


class TestNewsSourceBehavior:
    def test_enable_marks_active_and_emits_event(self, news_source: NewsSource) -> None:
        news_source.is_active = False
        news_source.enable()
        assert news_source.is_active is True
        events = news_source.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], SourceEnabled)
        assert events[0].source_id == news_source.id

    def test_disable_marks_inactive_and_emits_event(self, news_source: NewsSource) -> None:
        news_source.disable(reason="API changed")
        assert news_source.is_active is False
        events = news_source.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], SourceDisabled)
        assert events[0].source_id == news_source.id
        assert events[0].reason == "API changed"

    def test_enable_already_active(self, news_source: NewsSource) -> None:
        assert news_source.is_active is True
        news_source.enable()
        assert news_source.is_active is True
        events = news_source.pull_events()
        assert len(events) == 1  # still emits the event

    def test_disable_already_inactive(self, news_source: NewsSource) -> None:
        news_source.disable(reason="first")
        assert news_source.is_active is False
        news_source.pull_events()  # clear
        news_source.disable(reason="second")
        assert news_source.is_active is False  # stays inactive
        events = news_source.pull_events()
        assert len(events) == 1  # still emits

    def test_change_url(self, news_source: NewsSource) -> None:
        new_url = SourceUrl("https://new-url.com")
        news_source.change_url(new_url)
        assert news_source.source_url == new_url

    def test_change_source_type(self, news_source: NewsSource) -> None:
        news_source.change_source_type(SourceType.API)
        assert news_source.source_type == SourceType.API

    def test_assign_category(self, news_source: NewsSource) -> None:
        cat_id = CategoryId.generate()
        news_source.assign_category(cat_id)
        assert cat_id in news_source.categories
        assert len(news_source.categories) == 1

    def test_assign_category_duplicate(self, news_source: NewsSource) -> None:
        cat_id = CategoryId.generate()
        news_source.assign_category(cat_id)
        news_source.assign_category(cat_id)
        assert len(news_source.categories) == 1

    def test_remove_category(self, news_source: NewsSource) -> None:
        cat_id = CategoryId.generate()
        news_source.assign_category(cat_id)
        news_source.remove_category(cat_id)
        assert cat_id not in news_source.categories

    def test_remove_nonexistent_category(self, news_source: NewsSource) -> None:
        cat_id = CategoryId.generate()
        news_source.remove_category(cat_id)  # should not raise

    def test_assign_topic(self, news_source: NewsSource) -> None:
        topic_id = TopicId.generate()
        news_source.assign_topic(topic_id)
        assert topic_id in news_source.topics
        assert len(news_source.topics) == 1

    def test_assign_topic_duplicate(self, news_source: NewsSource) -> None:
        topic_id = TopicId.generate()
        news_source.assign_topic(topic_id)
        news_source.assign_topic(topic_id)
        assert len(news_source.topics) == 1

    def test_remove_topic(self, news_source: NewsSource) -> None:
        topic_id = TopicId.generate()
        news_source.assign_topic(topic_id)
        news_source.remove_topic(topic_id)
        assert topic_id not in news_source.topics

    def test_remove_nonexistent_topic(self, news_source: NewsSource) -> None:
        topic_id = TopicId.generate()
        news_source.remove_topic(topic_id)  # should not raise

    def test_multiple_categories_and_topics(self, news_source: NewsSource) -> None:
        cat1 = CategoryId.generate()
        cat2 = CategoryId.generate()
        top1 = TopicId.generate()
        top2 = TopicId.generate()
        news_source.assign_category(cat1)
        news_source.assign_category(cat2)
        news_source.assign_topic(top1)
        news_source.assign_topic(top2)
        assert len(news_source.categories) == 2
        assert len(news_source.topics) == 2


class TestNewsSourceEvents:
    def test_pull_events_clears_storage(self, news_source: NewsSource) -> None:
        news_source.disable(reason="test")
        events_first = news_source.pull_events()
        events_second = news_source.pull_events()
        assert len(events_first) == 1
        assert len(events_second) == 0

    def test_multiple_events_accumulated(self, news_source: NewsSource) -> None:
        news_source.disable(reason="first")
        news_source.enable()
        events = news_source.pull_events()
        assert len(events) == 2
        assert isinstance(events[0], SourceDisabled)
        assert isinstance(events[1], SourceEnabled)

    def test_register_event_requires_domain_event(self, news_source: NewsSource) -> None:
        with pytest.raises(TypeError):
            news_source.register_event("not an event")  # type: ignore[arg-type]
