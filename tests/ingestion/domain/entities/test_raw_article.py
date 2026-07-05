"""
Tests for RawArticle aggregate root (immutable).

Covers:
  - Construction (valid/invalid)
  - Invariants (I-11 to I-17)
  - Immutability
  - Property accessors
  - Equality and hash
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from foundation.base.entity import Entity

from ingestion.domain.entities.ids import FeedId, RawArticleId
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language


class TestRawArticleCreation:
    def test_create_valid_article(self, raw_article: RawArticle) -> None:
        assert raw_article.id is not None
        assert raw_article.feed_id is not None
        assert raw_article.external_id == "ext-123"
        assert raw_article.content_hash == "a" * 64
        assert raw_article.title is not None
        assert raw_article.url is not None
        assert raw_article.author == "Test Author"
        assert raw_article.language is not None
        assert raw_article.published_at is not None
        assert raw_article.fetched_at is not None
        assert raw_article.content_preview == "This is a preview"
        assert raw_article.metadata == {"source": "test"}

    def test_create_minimal_article(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        article = RawArticle(
            id=raw_article_id,
            feed_id=feed_id,
            external_id="ext-456",
            content_hash="b" * 64,
            title=article_title,
            url=valid_article_url,
        )
        assert article.author is None
        assert article.language is None
        assert article.published_at is None
        assert article.fetched_at is None
        assert article.content_preview is None
        assert article.metadata is None

    def test_inherits_entity(self, raw_article: RawArticle) -> None:
        assert isinstance(raw_article, Entity)

    def test_does_not_inherit_aggregate_root(self, raw_article: RawArticle) -> None:
        # RawArticle hereda de Entity, NO de AggregateRoot (ADR-023)
        from foundation.base.aggregate_root import AggregateRoot
        assert not isinstance(raw_article, AggregateRoot)

    def test_equality_by_id(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        article1 = RawArticle(
            id=raw_article_id,
            feed_id=feed_id,
            external_id="ext-1",
            content_hash="a" * 64,
            title=article_title,
            url=valid_article_url,
        )
        article2 = RawArticle(
            id=raw_article_id,
            feed_id=FeedId.generate(),
            external_id="ext-2",
            content_hash="b" * 64,
            title=ArticleTitle("Other"),
            url=ArticleUrl("https://other.com"),
        )
        assert article1 == article2

    def test_inequality(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        article1 = RawArticle(
            id=raw_article_id,
            feed_id=feed_id,
            external_id="ext-1",
            content_hash="a" * 64,
            title=article_title,
            url=valid_article_url,
        )
        article2 = RawArticle(
            id=RawArticleId.generate(),
            feed_id=feed_id,
            external_id="ext-1",
            content_hash="a" * 64,
            title=article_title,
            url=valid_article_url,
        )
        assert article1 != article2


class TestRawArticleInvariants:
    def test_fetched_at_before_published_raises(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        with pytest.raises(ValueError, match="fetched_at must be >= published_at"):
            RawArticle(
                id=raw_article_id,
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="a" * 64,
                title=article_title,
                url=valid_article_url,
                published_at=datetime(2024, 1, 5, tzinfo=timezone.utc),
                fetched_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

    def test_fetched_at_equal_to_published_allowed(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        now = datetime.now(timezone.utc)
        article = RawArticle(
            id=raw_article_id,
            feed_id=feed_id,
            external_id="ext-1",
            content_hash="a" * 64,
            title=article_title,
            url=valid_article_url,
            published_at=now,
            fetched_at=now,
        )
        assert article.published_at == article.fetched_at

    def test_invalid_content_hash_raises(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        with pytest.raises(ValueError, match="valid SHA-256"):
            RawArticle(
                id=raw_article_id,
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="not-a-hash",
                title=article_title,
                url=valid_article_url,
            )

    def test_content_hash_too_short_raises(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        with pytest.raises(ValueError, match="valid SHA-256"):
            RawArticle(
                id=raw_article_id,
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="abc123",
                title=article_title,
                url=valid_article_url,
            )

    def test_content_hash_with_uppercase_raises(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        with pytest.raises(ValueError, match="valid SHA-256"):
            RawArticle(
                id=raw_article_id,
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="A" + "a" * 63,
                title=article_title,
                url=valid_article_url,
            )


class TestRawArticleImmutability:
    def test_frozen_instance(
        self,
        raw_article_id: RawArticleId,
        feed_id: FeedId,
        article_title: ArticleTitle,
        valid_article_url: ArticleUrl,
    ) -> None:
        article = RawArticle(
            id=raw_article_id,
            feed_id=feed_id,
            external_id="ext-1",
            content_hash="a" * 64,
            title=article_title,
            url=valid_article_url,
        )
        with pytest.raises(Exception):
            article.external_id = "changed"

    def test_no_events_attribute(self, raw_article: RawArticle) -> None:
        assert not hasattr(raw_article, "_events")
        assert not hasattr(raw_article, "register_event")
        assert not hasattr(raw_article, "pull_events")


class TestRawArticleProperties:
    def test_article_url_property(self, raw_article: RawArticle) -> None:
        assert isinstance(raw_article.article_url, ArticleUrl)
        assert raw_article.article_url == raw_article.url

    def test_article_title_property(self, raw_article: RawArticle) -> None:
        assert isinstance(raw_article.article_title, ArticleTitle)
        assert raw_article.article_title == raw_article.title
