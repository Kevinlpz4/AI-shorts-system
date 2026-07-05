"""
Tests for Feed aggregate root.

Covers:
  - Construction (valid/invalid)
  - Invariants (I-05 to I-10)
  - Behavior (record_collection, record_failure, can_retry, pause, activate)
  - Domain events (RawArticleCollected)
  - Category/topic management
  - Sync policy update
  - Equality and hash
"""

from __future__ import annotations

from uuid import UUID

import pytest

from foundation.base.aggregate_root import AggregateRoot
from foundation.base.entity import Entity

from ingestion.domain.entities.feed import Feed, FeedFailureResult
from ingestion.domain.entities.ids import CategoryId, FeedId, SourceId, TopicId
from ingestion.domain.events.ingestion_events import RawArticleCollected
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


class TestFeedCreation:
    def test_create_valid_feed(self, feed: Feed) -> None:
        assert feed.id is not None
        assert feed.source_id is not None
        assert feed.url is not None
        assert feed.label is not None
        assert feed.language is not None
        assert feed.is_active is True
        assert feed.retry_count == 0
        assert feed.categories == []
        assert feed.topics == []

    def test_inherits_aggregate_root(self, feed: Feed) -> None:
        assert isinstance(feed, AggregateRoot)
        assert isinstance(feed, Entity)

    def test_default_sync_policy(self, feed: Feed) -> None:
        assert feed.sync_policy.mode == SyncMode.PULL
        assert feed.sync_policy.interval_minutes == 30

    def test_equality_by_id(
        self,
        feed_id: FeedId,
        source_id: SourceId,
        valid_article_url: ArticleUrl,
        article_title: ArticleTitle,
        language_en: Language,
        sync_policy_pull: SyncPolicy,
    ) -> None:
        feed1 = Feed(
            id=feed_id,
            source_id=source_id,
            url=valid_article_url,
            label=article_title,
            language=language_en,
            sync_policy=sync_policy_pull,
        )
        feed2 = Feed(
            id=feed_id,
            source_id=SourceId.generate(),
            url=ArticleUrl("https://other.com"),
            label=ArticleTitle("Other"),
            language=Language("es"),
            sync_policy=sync_policy_pull,
        )
        assert feed1 == feed2

    def test_inequality(
        self,
        feed_id: FeedId,
        source_id: SourceId,
        valid_article_url: ArticleUrl,
        article_title: ArticleTitle,
        language_en: Language,
        sync_policy_pull: SyncPolicy,
    ) -> None:
        feed1 = Feed(
            id=feed_id,
            source_id=source_id,
            url=valid_article_url,
            label=article_title,
            language=language_en,
            sync_policy=sync_policy_pull,
        )
        feed2 = Feed(
            id=FeedId.generate(),
            source_id=source_id,
            url=valid_article_url,
            label=article_title,
            language=language_en,
            sync_policy=sync_policy_pull,
        )
        assert feed1 != feed2


class TestFeedCollectionAndRetry:
    def test_record_collection_resets_retry_count(self, feed: Feed) -> None:
        feed.retry_count = 3
        feed.record_collection(count=5)
        assert feed.retry_count == 0

    def test_record_collection_emits_event_when_count_positive(
        self, feed: Feed, batch_id: UUID
    ) -> None:
        feed.record_collection(batch_id=batch_id, count=5)
        events = feed.pull_events()
        assert len(events) == 1
        assert isinstance(events[0], RawArticleCollected)
        assert events[0].feed_id == feed.id
        assert events[0].batch_id == batch_id
        assert events[0].count == 5

    def test_record_collection_does_not_emit_when_count_zero(
        self, feed: Feed, batch_id: UUID
    ) -> None:
        feed.record_collection(batch_id=batch_id, count=0)
        events = feed.pull_events()
        assert len(events) == 0

    def test_record_failure_increments_retry_count(self, feed: Feed) -> None:
        result = feed.record_failure("Timeout")
        assert result.retry_count == 1
        assert result.paused is False
        assert feed.retry_count == 1

    def test_record_failure_pauses_when_max_exceeded(
        self, feed: Feed
    ) -> None:
        feed.sync_policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
            max_retries=2,
        )
        feed.record_failure("error 1")  # retry_count=1
        feed.record_failure("error 2")  # retry_count=2, not paused (can_retry)
        result = feed.record_failure("error 3")  # retry_count=3, paused
        assert result.retry_count == 3
        assert result.paused is True
        assert feed.is_active is False

    def test_can_retry_returns_true_when_below_max(self, feed: Feed) -> None:
        feed.sync_policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
            max_retries=3,
        )
        feed.retry_count = 2
        assert feed.can_retry() is True

    def test_can_retry_returns_false_when_at_max(self, feed: Feed) -> None:
        feed.sync_policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
            max_retries=3,
        )
        feed.retry_count = 3
        assert feed.can_retry() is False

    def test_can_retry_returns_false_when_over_max(self, feed: Feed) -> None:
        feed.sync_policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
            max_retries=3,
        )
        feed.retry_count = 5
        assert feed.can_retry() is False

    def test_feed_failure_result_dataclass(self) -> None:
        result = FeedFailureResult(paused=True, retry_count=5)
        assert result.paused is True
        assert result.retry_count == 5
        assert FeedFailureResult(paused=True, retry_count=5) == FeedFailureResult(
            paused=True, retry_count=5
        )
        assert FeedFailureResult(paused=False, retry_count=1) != FeedFailureResult(
            paused=True, retry_count=1
        )


class TestFeedState:
    def test_pause_marks_inactive(self, feed: Feed) -> None:
        feed.pause(reason="Manual maintenance")
        assert feed.is_active is False

    def test_activate_marks_active_and_resets_retry(self, feed: Feed) -> None:
        feed.is_active = False
        feed.retry_count = 5
        feed.activate()
        assert feed.is_active is True
        assert feed.retry_count == 0

    def test_activate_on_already_active(self, feed: Feed) -> None:
        feed.retry_count = 2
        feed.activate()
        assert feed.is_active is True
        assert feed.retry_count == 0


class TestFeedCategoryTopic:
    def test_assign_category(self, feed: Feed) -> None:
        cat_id = CategoryId.generate()
        feed.assign_category(cat_id)
        assert cat_id in feed.categories
        assert len(feed.categories) == 1

    def test_assign_category_duplicate(self, feed: Feed) -> None:
        cat_id = CategoryId.generate()
        feed.assign_category(cat_id)
        feed.assign_category(cat_id)
        assert len(feed.categories) == 1

    def test_remove_category(self, feed: Feed) -> None:
        cat_id = CategoryId.generate()
        feed.assign_category(cat_id)
        feed.remove_category(cat_id)
        assert cat_id not in feed.categories

    def test_remove_nonexistent_category(self, feed: Feed) -> None:
        feed.remove_category(CategoryId.generate())

    def test_assign_topic(self, feed: Feed) -> None:
        topic_id = TopicId.generate()
        feed.assign_topic(topic_id)
        assert topic_id in feed.topics
        assert len(feed.topics) == 1

    def test_assign_topic_duplicate(self, feed: Feed) -> None:
        topic_id = TopicId.generate()
        feed.assign_topic(topic_id)
        feed.assign_topic(topic_id)
        assert len(feed.topics) == 1

    def test_remove_topic(self, feed: Feed) -> None:
        topic_id = TopicId.generate()
        feed.assign_topic(topic_id)
        feed.remove_topic(topic_id)
        assert topic_id not in feed.topics

    def test_multiple_categories_and_topics(self, feed: Feed) -> None:
        cat1 = CategoryId.generate()
        cat2 = CategoryId.generate()
        top1 = TopicId.generate()
        feed.assign_category(cat1)
        feed.assign_category(cat2)
        feed.assign_topic(top1)
        assert len(feed.categories) == 2
        assert len(feed.topics) == 1


class TestFeedSyncPolicy:
    def test_update_sync_policy(self, feed: Feed) -> None:
        new_policy = SyncPolicy(
            mode=SyncMode.PUSH,
            max_retries=5,
        )
        feed.update_sync_policy(new_policy)
        assert feed.sync_policy.mode == SyncMode.PUSH
        assert feed.sync_policy.max_retries == 5


class TestFeedEvents:
    def test_pull_events_clears_storage(self, feed: Feed) -> None:
        feed.record_collection(count=3)
        events_first = feed.pull_events()
        events_second = feed.pull_events()
        assert len(events_first) == 1
        assert len(events_second) == 0

    def test_multiple_collections_accumulate_events(self, feed: Feed) -> None:
        feed.record_collection(count=2)
        feed.record_collection(count=3)
        events = feed.pull_events()
        assert len(events) == 2
        assert all(isinstance(e, RawArticleCollected) for e in events)
