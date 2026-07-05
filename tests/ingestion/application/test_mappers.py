"""Tests for all Mappers — 5 mappers, domain entity → DTO conversion."""

from __future__ import annotations

from datetime import datetime, timezone

from foundation.entity_id import EntityId

from ingestion.application.dto import (
    CategoryDetailDTO,
    CategorySummaryDTO,
    FeedDetailDTO,
    FeedSummaryDTO,
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
    SourceDetailDTO,
    SourceSummaryDTO,
    TopicDetailDTO,
    TopicSummaryDTO,
)
from ingestion.application.mappers import (
    CategoryMapper,
    FeedMapper,
    RawArticleMapper,
    SourceMapper,
    TopicMapper,
)
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


# ── Helpers ──


def _make_id(id_cls: type[EntityId], suffix: str = "") -> EntityId:
    """Create an ID deterministically using from_string."""
    return id_cls.from_string(f"00000000-0000-0000-0000-00000000000{suffix}")  # type: ignore[arg-type]


# ── SourceMapper Tests ──


class TestSourceMapper:
    """SourceMapper → NewsSource → SourceSummaryDTO / SourceDetailDTO."""

    def test_to_summary(self) -> None:
        source = NewsSource(
            id=_make_id(SourceId, "1"),  # type: ignore[arg-type]
            name="Reddit",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://reddit.com"),
        )
        dto = SourceMapper.to_summary(source)
        assert isinstance(dto, SourceSummaryDTO)
        assert dto.name == "Reddit"
        assert dto.source_type == "RSS"
        assert dto.source_url == "https://reddit.com"
        assert dto.is_active is True

    def test_to_detail(self) -> None:
        cat_id = _make_id(CategoryId, "1")  # type: ignore[arg-type]
        top_id = _make_id(TopicId, "2")  # type: ignore[arg-type]
        source = NewsSource(
            id=_make_id(SourceId, "1"),  # type: ignore[arg-type]
            name="Reddit",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://reddit.com"),
            categories=[cat_id],  # type: ignore[arg-type]
            topics=[top_id],  # type: ignore[arg-type]
        )
        dto = SourceMapper.to_detail(source)
        assert isinstance(dto, SourceDetailDTO)
        assert len(dto.categories) == 1
        assert len(dto.topics) == 1
        assert str(cat_id) in dto.categories
        assert str(top_id) in dto.topics

    def test_to_detail_empty_relations(self) -> None:
        source = NewsSource(
            id=_make_id(SourceId, "1"),  # type: ignore[arg-type]
            name="Test",
            source_type=SourceType.API,
            source_url=SourceUrl("https://api.test.com"),
        )
        dto = SourceMapper.to_detail(source)
        assert dto.categories == ()
        assert dto.topics == ()


# ── FeedMapper Tests ──


class TestFeedMapper:
    """FeedMapper → Feed → FeedSummaryDTO / FeedDetailDTO."""

    def _make_feed(self, **kwargs) -> Feed:
        defaults = {
            "id": _make_id(FeedId, "1"),  # type: ignore[arg-type]
            "source_id": _make_id(SourceId, "2"),  # type: ignore[arg-type]
            "url": ArticleUrl("https://example.com/feed"),
            "label": ArticleTitle("Tech News"),
            "language": Language("en"),
        }
        defaults.update(kwargs)
        return Feed(**defaults)  # type: ignore[arg-type]

    def test_to_summary(self) -> None:
        feed = self._make_feed(retry_count=3)
        dto = FeedMapper.to_summary(feed)
        assert isinstance(dto, FeedSummaryDTO)
        assert dto.label == "Tech News"
        assert dto.language == "en"
        assert dto.retry_count == 3
        assert dto.is_active is True

    def test_to_summary_inactive(self) -> None:
        feed = self._make_feed(is_active=False)
        dto = FeedMapper.to_summary(feed)
        assert dto.is_active is False

    def test_to_detail(self) -> None:
        cat_id = _make_id(CategoryId, "1")  # type: ignore[arg-type]
        top_id = _make_id(TopicId, "2")  # type: ignore[arg-type]
        feed = self._make_feed(
            sync_policy=SyncPolicy(
                mode=SyncMode.PULL,
                interval_minutes=60,
                max_retries=5,
            ),
            categories=[cat_id],  # type: ignore[arg-type]
            topics=[top_id],  # type: ignore[arg-type]
            retry_count=2,
        )
        dto = FeedMapper.to_detail(feed)
        assert isinstance(dto, FeedDetailDTO)
        assert dto.sync_mode == "PULL"
        assert dto.sync_interval_minutes == 60
        assert dto.sync_max_retries == 5
        assert len(dto.categories) == 1
        assert len(dto.topics) == 1
        assert dto.retry_count == 2

    def test_to_detail_policy_defaults(self) -> None:
        feed = self._make_feed()
        dto = FeedMapper.to_detail(feed)
        assert dto.sync_mode == "PULL"
        assert dto.sync_interval_minutes == 30
        assert dto.sync_max_retries == 3


# ── RawArticleMapper Tests ──


class TestRawArticleMapper:
    """RawArticleMapper → RawArticle → RawArticleSummaryDTO / RawArticleDetailDTO."""

    def _make_article(self, **kwargs) -> RawArticle:
        now = datetime.now(timezone.utc)
        defaults = {
            "id": _make_id(RawArticleId, "1"),  # type: ignore[arg-type]
            "feed_id": _make_id(FeedId, "2"),  # type: ignore[arg-type]
            "external_id": "ext-123",
            "content_hash": "a" * 64,
            "title": ArticleTitle("Test Article"),
            "url": ArticleUrl("https://example.com/article"),
            "fetched_at": now,
        }
        defaults.update(kwargs)
        return RawArticle(**defaults)  # type: ignore[arg-type]

    def test_to_summary(self) -> None:
        article = self._make_article(author="John", language=Language("en"))
        dto = RawArticleMapper.to_summary(article)
        assert isinstance(dto, RawArticleSummaryDTO)
        assert dto.title == "Test Article"
        assert dto.author == "John"
        assert dto.language == "en"

    def test_to_summary_no_optional(self) -> None:
        article = self._make_article()
        dto = RawArticleMapper.to_summary(article)
        assert dto.author is None
        assert dto.language is None
        assert dto.published_at is None

    def test_to_detail(self) -> None:
        now = datetime.now(timezone.utc)
        article = self._make_article(
            author="Jane",
            language=Language("es"),
            published_at=now,
            content_preview="Preview...",
            metadata={"key": "val"},
        )
        dto = RawArticleMapper.to_detail(article)
        assert isinstance(dto, RawArticleDetailDTO)
        assert dto.external_id == "ext-123"
        assert dto.content_hash == "a" * 64
        assert dto.author == "Jane"
        assert dto.language == "es"
        assert dto.published_at == now
        assert dto.content_preview == "Preview..."
        assert dto.metadata == {"key": "val"}

    def test_to_detail_no_optional(self) -> None:
        article = self._make_article()
        dto = RawArticleMapper.to_detail(article)
        assert dto.author is None
        assert dto.metadata is None
        assert dto.content_preview is None


# ── CategoryMapper Tests ──


class TestCategoryMapper:
    """CategoryMapper → Category → CategorySummaryDTO / CategoryDetailDTO."""

    def test_to_summary(self) -> None:
        cat = Category(
            id=_make_id(CategoryId, "1"),  # type: ignore[arg-type]
            name=CategoryName("Technology"),
            slug="technology",
        )
        dto = CategoryMapper.to_summary(cat)
        assert isinstance(dto, CategorySummaryDTO)
        assert dto.name == "Technology"
        assert dto.slug == "technology"
        assert dto.is_active is True

    def test_to_detail_without_parent(self) -> None:
        cat = Category(
            id=_make_id(CategoryId, "1"),  # type: ignore[arg-type]
            name=CategoryName("Tech"),
            slug="tech",
        )
        dto = CategoryMapper.to_detail(cat)
        assert isinstance(dto, CategoryDetailDTO)
        assert dto.parent_id is None

    def test_to_detail_with_parent(self) -> None:
        parent_id = _make_id(CategoryId, "1")  # type: ignore[arg-type]
        cat = Category(
            id=_make_id(CategoryId, "2"),  # type: ignore[arg-type]
            name=CategoryName("Python"),
            slug="python",
            parent_id=parent_id,  # type: ignore[arg-type]
        )
        dto = CategoryMapper.to_detail(cat)
        assert dto.parent_id is not None
        assert dto.parent_id == str(parent_id)

    def test_to_detail_inactive(self) -> None:
        cat = Category(
            id=_make_id(CategoryId, "1"),  # type: ignore[arg-type]
            name=CategoryName("Old"),
            slug="old",
            is_active=False,
        )
        dto = CategoryMapper.to_detail(cat)
        assert dto.is_active is False


# ── TopicMapper Tests ──


class TestTopicMapper:
    """TopicMapper → Topic → TopicSummaryDTO / TopicDetailDTO."""

    def _make_topic(self, **kwargs) -> Topic:
        defaults = {
            "id": _make_id(TopicId, "1"),  # type: ignore[arg-type]
            "name": "AI",
        }
        defaults.update(kwargs)
        return Topic(**defaults)  # type: ignore[arg-type]

    def test_to_summary(self) -> None:
        topic = self._make_topic()
        dto = TopicMapper.to_summary(topic)
        assert isinstance(dto, TopicSummaryDTO)
        assert dto.name == "AI"
        assert dto.is_active is True

    def test_to_detail_without_description(self) -> None:
        topic = self._make_topic()
        dto = TopicMapper.to_detail(topic)
        assert isinstance(dto, TopicDetailDTO)
        assert dto.description is None

    def test_to_detail_with_description(self) -> None:
        topic = self._make_topic(description="Artificial Intelligence")
        dto = TopicMapper.to_detail(topic)
        assert dto.description == "Artificial Intelligence"

    def test_to_detail_inactive(self) -> None:
        topic = self._make_topic(is_active=False)
        dto = TopicMapper.to_detail(topic)
        assert dto.is_active is False
