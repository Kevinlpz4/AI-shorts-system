"""
Test fixtures for Ingestion Domain Core tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path for ingestion domain imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from ingestion.domain.entities.category import Category
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    RawArticleId,
    SourceId,
    TopicId,
)
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.entities.topic import Topic
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


# ── Sample IDs ──


@pytest.fixture
def source_id() -> SourceId:
    return SourceId.generate()


@pytest.fixture
def feed_id() -> FeedId:
    return FeedId.generate()


@pytest.fixture
def raw_article_id() -> RawArticleId:
    return RawArticleId.generate()


@pytest.fixture
def category_id() -> CategoryId:
    return CategoryId.generate()


@pytest.fixture
def topic_id() -> TopicId:
    return TopicId.generate()


# ── Sample URLs ──


@pytest.fixture
def valid_source_url() -> SourceUrl:
    return SourceUrl("https://www.reddit.com")


@pytest.fixture
def valid_article_url() -> ArticleUrl:
    return ArticleUrl("https://www.reddit.com/r/programming/posts/123")


# ── Sample Value Objects ──


@pytest.fixture
def article_title() -> ArticleTitle:
    return ArticleTitle("Test Article Title")


@pytest.fixture
def language_en() -> Language:
    return Language("en")


@pytest.fixture
def language_es() -> Language:
    return Language("es")


@pytest.fixture
def category_name() -> CategoryName:
    return CategoryName("Technology")


@pytest.fixture
def sync_policy_pull() -> SyncPolicy:
    return SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, max_retries=3)


@pytest.fixture
def sync_policy_push() -> SyncPolicy:
    return SyncPolicy(mode=SyncMode.PUSH)


# ── Sample Entities ──


@pytest.fixture
def news_source(
    source_id: SourceId,
    valid_source_url: SourceUrl,
) -> NewsSource:
    return NewsSource(
        id=source_id,
        name="Reddit",
        source_type=SourceType.SOCIAL_MEDIA,
        source_url=valid_source_url,
    )


@pytest.fixture
def feed(
    feed_id: FeedId,
    source_id: SourceId,
    valid_article_url: ArticleUrl,
    article_title: ArticleTitle,
    language_en: Language,
    sync_policy_pull: SyncPolicy,
) -> Feed:
    return Feed(
        id=feed_id,
        source_id=source_id,
        url=valid_article_url,
        label=article_title,
        language=language_en,
        sync_policy=sync_policy_pull,
    )


@pytest.fixture
def raw_article(
    raw_article_id: RawArticleId,
    feed_id: FeedId,
    article_title: ArticleTitle,
    valid_article_url: ArticleUrl,
) -> RawArticle:
    return RawArticle(
        id=raw_article_id,
        feed_id=feed_id,
        external_id="ext-123",
        content_hash="a" * 64,
        title=article_title,
        url=valid_article_url,
        author="Test Author",
        language=Language("en"),
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        fetched_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        content_preview="This is a preview",
        metadata={"source": "test"},
    )


@pytest.fixture
def category(category_id: CategoryId, category_name: CategoryName) -> Category:
    return Category(
        id=category_id,
        name=category_name,
        slug="technology",
    )


@pytest.fixture
def topic(topic_id: TopicId) -> Topic:
    return Topic(
        id=topic_id,
        name="Artificial Intelligence",
        description="AI and ML topics",
    )


# ── Sample UUID ──


@pytest.fixture
def batch_id() -> UUID:
    return uuid4()
