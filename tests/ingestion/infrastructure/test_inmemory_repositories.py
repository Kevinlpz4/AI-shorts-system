"""
Tests for InMemory repositories — each repository tested independently.

Verifies that all repository methods:
    - Return correct results for save + find round trips.
    - Return Result.failure with correct error codes for not-found cases.
    - Return correct boolean values for existence checks.
    - Filter correctly (active/inactive, by source, etc.).
    - Handle pagination correctly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from foundation.result.result import Success, Failure

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
from ingestion.domain.exceptions import InvalidStateError
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy
from ingestion.infrastructure.inmemory.repositories import (
    InMemoryCategoryRepository,
    InMemoryFeedRepository,
    InMemoryNewsSourceRepository,
    InMemoryRawArticleRepository,
    InMemoryTopicRepository,
)


# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════


def make_source(
    name: str = "TestSource",
    source_type: SourceType = SourceType.RSS,
    source_url: str = "https://example.com",
    is_active: bool = True,
) -> NewsSource:
    return NewsSource(
        id=SourceId.generate(),
        name=name,
        source_type=source_type,
        source_url=SourceUrl(source_url),
        is_active=is_active,
    )


def make_feed(
    source_id: SourceId | None = None,
    url: str = "https://example.com/feed",
    label: str = "Test Feed",
    is_active: bool = True,
) -> Feed:
    return Feed(
        id=FeedId.generate(),
        source_id=source_id or SourceId.generate(),
        url=ArticleUrl(url),
        label=ArticleTitle(label),
        language=Language("en"),
        is_active=is_active,
        sync_policy=SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
        ),
    )


_article_counter: int = 0


def make_article(
    feed_id: FeedId | None = None,
    external_id: str | None = None,
    content_hash: str | None = None,
    title: str = "Test Article",
    url: str | None = None,
) -> RawArticle:
    global _article_counter
    _article_counter += 1
    # Generate unique defaults to avoid duplicate collisions
    ext_id = external_id or f"ext-{_article_counter}"
    c_hash = content_hash or f"{_article_counter:064x}"
    art_url = url or f"https://example.com/article-{_article_counter}"
    return RawArticle(
        id=RawArticleId.generate(),
        feed_id=feed_id or FeedId.generate(),
        external_id=ext_id,
        content_hash=c_hash,
        title=ArticleTitle(title),
        url=ArticleUrl(art_url),
        fetched_at=datetime(2026, 7, 5, tzinfo=timezone.utc),
    )


def make_category(
    name: str = "Tech",
    slug: str = "tech",
    parent_id: CategoryId | None = None,
    is_active: bool = True,
) -> Category:
    return Category(
        id=CategoryId.generate(),
        name=CategoryName(name),
        slug=slug,
        parent_id=parent_id,
        is_active=is_active,
    )


def make_topic(
    name: str = "AI",
    is_active: bool = True,
) -> Topic:
    return Topic(
        id=TopicId.generate(),
        name=name,
        is_active=is_active,
    )


# ═══════════════════════════════════════════════════
# InMemoryNewsSourceRepository Tests
# ═══════════════════════════════════════════════════


class TestInMemoryNewsSourceRepository:
    """Test suite for InMemoryNewsSourceRepository."""

    def test_save_and_find_by_id(self) -> None:
        """save + find_by_id debe retornar el mismo source."""
        repo = InMemoryNewsSourceRepository()
        source = make_source(name="Reddit")
        repo.save(source)

        result = repo.find_by_id(source.id)
        assert result.is_success
        assert result.value.name == "Reddit"
        assert result.value.is_active is True

    def test_find_by_id_not_found(self) -> None:
        """find_by_id debe retornar Failure si no existe."""
        repo = InMemoryNewsSourceRepository()
        result = repo.find_by_id(SourceId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_find_by_name(self) -> None:
        """find_by_name debe retornar el source por nombre."""
        repo = InMemoryNewsSourceRepository()
        source = make_source(name="UniqueName")
        repo.save(source)

        result = repo.find_by_name("UniqueName")
        assert result.is_success
        assert result.value.name == "UniqueName"

    def test_find_by_name_not_found(self) -> None:
        """find_by_name debe retornar Failure si no existe."""
        repo = InMemoryNewsSourceRepository()
        result = repo.find_by_name("NonExistent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_exists_by_name(self) -> None:
        """exists_by_name debe retornar True si existe."""
        repo = InMemoryNewsSourceRepository()
        repo.save(make_source(name="Existing"))
        assert repo.exists_by_name("Existing") is True
        assert repo.exists_by_name("NonExistent") is False

    def test_find_all(self) -> None:
        """find_all debe retornar todos los sources."""
        repo = InMemoryNewsSourceRepository()
        repo.save(make_source(name="A"))
        repo.save(make_source(name="B"))
        assert len(repo.find_all()) == 2

    def test_find_active(self) -> None:
        """find_active debe retornar solo los activos."""
        repo = InMemoryNewsSourceRepository()
        repo.save(make_source(name="Active1", is_active=True))
        repo.save(make_source(name="Active2", is_active=True))
        repo.save(make_source(name="Inactive", is_active=False))
        actives = repo.find_active()
        assert len(actives) == 2
        assert all(s.is_active for s in actives)


# ═══════════════════════════════════════════════════
# InMemoryFeedRepository Tests
# ═══════════════════════════════════════════════════


class TestInMemoryFeedRepository:
    """Test suite for InMemoryFeedRepository."""

    def test_save_and_find_by_id(self) -> None:
        """save + find_by_id debe retornar el mismo feed."""
        repo = InMemoryFeedRepository()
        feed = make_feed(label="My Feed")
        repo.save(feed)

        result = repo.find_by_id(feed.id)
        assert result.is_success
        assert result.value.label.value == "My Feed"

    def test_find_by_id_not_found(self) -> None:
        """find_by_id debe retornar Failure si no existe."""
        repo = InMemoryFeedRepository()
        result = repo.find_by_id(FeedId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND

    def test_find_by_source(self) -> None:
        """find_by_source debe retornar feeds de un source."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        repo.save(make_feed(source_id=sid, label="Feed1"))
        repo.save(make_feed(source_id=sid, label="Feed2"))
        other_sid = SourceId.generate()
        repo.save(make_feed(source_id=other_sid, label="Other"))

        feeds = repo.find_by_source(sid)
        assert len(feeds) == 2

    def test_find_by_url(self) -> None:
        """find_by_url debe retornar el feed por URL dentro del source."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        feed = make_feed(
            source_id=sid,
            url="https://example.com/rss",
            label="Found",
        )
        repo.save(feed)

        result = repo.find_by_url(sid, ArticleUrl("https://example.com/rss"))
        assert result.is_success
        assert result.value.label.value == "Found"

    def test_find_by_url_not_found(self) -> None:
        """find_by_url debe retornar Failure si no existe."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        result = repo.find_by_url(sid, ArticleUrl("https://example.com/rss"))
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND

    def test_find_active_by_source(self) -> None:
        """find_active_by_source debe retornar solo feeds activos."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        repo.save(make_feed(source_id=sid, label="Active1", is_active=True))
        repo.save(make_feed(source_id=sid, label="Active2", is_active=True))
        repo.save(make_feed(source_id=sid, label="Inactive", is_active=False))

        actives = repo.find_active_by_source(sid)
        assert len(actives) == 2
        assert all(f.is_active for f in actives)

    def test_exists_by_source_and_url(self) -> None:
        """exists_by_source_and_url retorna True si existe."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        repo.save(make_feed(source_id=sid, url="https://example.com/rss"))
        assert (
            repo.exists_by_source_and_url(
                sid, ArticleUrl("https://example.com/rss")
            )
            is True
        )
        assert (
            repo.exists_by_source_and_url(
                sid, ArticleUrl("https://other.com/rss")
            )
            is False
        )

    def test_count_active_by_source(self) -> None:
        """count_active_by_source retorna conteo correcto."""
        repo = InMemoryFeedRepository()
        sid = SourceId.generate()
        repo.save(make_feed(source_id=sid, is_active=True))
        repo.save(make_feed(source_id=sid, is_active=True))
        repo.save(make_feed(source_id=sid, is_active=False))
        assert repo.count_active_by_source(sid) == 2
        assert repo.count_active_by_source(SourceId.generate()) == 0


# ═══════════════════════════════════════════════════
# InMemoryRawArticleRepository Tests
# ═══════════════════════════════════════════════════


class TestInMemoryRawArticleRepository:
    """Test suite for InMemoryRawArticleRepository."""

    def test_save_and_find_by_id(self) -> None:
        """save + find_by_id debe retornar el mismo artículo."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        article = make_article(feed_id=fid, external_id="ext-1")
        repo.save(article)

        result = repo.find_by_id(article.id)
        assert result.is_success
        assert result.value.external_id == "ext-1"
        assert result.value.feed_id == fid

    def test_find_by_id_not_found(self) -> None:
        """find_by_id debe retornar Failure si no existe."""
        repo = InMemoryRawArticleRepository()
        result = repo.find_by_id(RawArticleId.generate())
        assert result.is_failure
        assert (
            result.error.code == IngestionErrorCode.RAW_ARTICLE_NOT_FOUND
        )

    def test_find_by_feed(self) -> None:
        """find_by_feed debe retornar artículos de un feed."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(make_article(feed_id=fid, external_id="ext-1"))
        repo.save(make_article(feed_id=fid, external_id="ext-2"))
        other_fid = FeedId.generate()
        repo.save(make_article(feed_id=other_fid, external_id="ext-3"))

        articles = repo.find_by_feed(fid)
        assert len(articles) == 2

    def test_find_by_feed_pagination(self) -> None:
        """find_by_feed debe paginar correctamente."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        for i in range(10):
            repo.save(
                make_article(
                    feed_id=fid,
                    external_id=f"ext-{i}",
                    content_hash=f"{i:01x}{'a' * 63}",
                )
            )

        page1 = repo.find_by_feed(fid, page=1, size=3)
        page2 = repo.find_by_feed(fid, page=2, size=3)
        assert len(page1) == 3
        assert len(page2) == 3
        # Ensure different pages return different results
        assert page1[0].external_id != page2[0].external_id

    def test_find_by_hash(self) -> None:
        """find_by_hash debe retornar artículo por hash."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        article = make_article(
            feed_id=fid,
            external_id="ext-1",
            content_hash="b" * 64,
        )
        repo.save(article)

        result = repo.find_by_hash(fid, "b" * 64)
        assert result.is_success
        assert result.value.external_id == "ext-1"

    def test_find_by_hash_not_found(self) -> None:
        """find_by_hash debe retornar Failure si no existe."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        result = repo.find_by_hash(fid, "c" * 64)
        assert result.is_failure
        assert (
            result.error.code == IngestionErrorCode.RAW_ARTICLE_NOT_FOUND
        )

    def test_exists_by_url(self) -> None:
        """exists_by_url debe retornar True si existe."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                url="https://example.com/article1",
            )
        )
        assert (
            repo.exists_by_url(fid, ArticleUrl("https://example.com/article1"))
            is True
        )
        assert (
            repo.exists_by_url(fid, ArticleUrl("https://other.com/article"))
            is False
        )

    def test_exists_by_hash(self) -> None:
        """exists_by_hash debe retornar True si existe."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="d" * 64,
            )
        )
        assert repo.exists_by_hash(fid, "d" * 64) is True
        assert repo.exists_by_hash(fid, "e" * 64) is False

    def test_count_by_feed(self) -> None:
        """count_by_feed retorna conteo correcto."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(make_article(feed_id=fid, external_id="ext-1"))
        repo.save(make_article(feed_id=fid, external_id="ext-2"))
        assert repo.count_by_feed(fid) == 2
        assert repo.count_by_feed(FeedId.generate()) == 0

    def test_duplicate_external_id_raises_error(self) -> None:
        """save debe lanzar InvalidStateError si external_id+feed_id duplicado."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="a" * 64,
                url="https://example.com/article-a",
            )
        )
        with pytest.raises(InvalidStateError) as excinfo:
            repo.save(
                make_article(
                    feed_id=fid,
                    external_id="ext-1",
                    content_hash="b" * 64,
                    url="https://example.com/article-b",
                )
            )
        assert "DUPLICATE_ARTICLE" in str(excinfo.value)

    def test_duplicate_content_hash_raises_error(self) -> None:
        """save debe lanzar InvalidStateError si content_hash+feed_id duplicado."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="c" * 64,
                url="https://example.com/article-c",
            )
        )
        with pytest.raises(InvalidStateError) as excinfo:
            repo.save(
                make_article(
                    feed_id=fid,
                    external_id="ext-2",
                    content_hash="c" * 64,
                    url="https://example.com/article-d",
                )
            )
        assert "DUPLICATE_ARTICLE" in str(excinfo.value)

    def test_save_batch(self) -> None:
        """save_batch debe guardar múltiples artículos."""
        repo = InMemoryRawArticleRepository()
        fid = FeedId.generate()
        articles = [
            make_article(
                feed_id=fid,
                external_id=f"ext-{i}",
                content_hash=f"{i:02x}{'a' * 62}",
            )
            for i in range(5)
        ]
        repo.save_batch(articles)
        assert repo.count_by_feed(fid) == 5


# ═══════════════════════════════════════════════════
# InMemoryCategoryRepository Tests
# ═══════════════════════════════════════════════════


class TestInMemoryCategoryRepository:
    """Test suite for InMemoryCategoryRepository."""

    def test_save_and_find_by_id(self) -> None:
        """save + find_by_id debe retornar la misma categoría."""
        repo = InMemoryCategoryRepository()
        cat = make_category(name="Tech", slug="tech")
        repo.save(cat)

        result = repo.find_by_id(cat.id)
        assert result.is_success
        assert result.value.name.value == "Tech"
        assert result.value.slug == "tech"

    def test_find_by_id_not_found(self) -> None:
        """find_by_id debe retornar Failure si no existe."""
        repo = InMemoryCategoryRepository()
        result = repo.find_by_id(CategoryId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    def test_find_by_slug(self) -> None:
        """find_by_slug debe retornar categoría por slug."""
        repo = InMemoryCategoryRepository()
        repo.save(make_category(name="Tech", slug="tech"))
        result = repo.find_by_slug("tech")
        assert result.is_success
        assert result.value.slug == "tech"

    def test_find_by_slug_not_found(self) -> None:
        """find_by_slug debe retornar Failure si no existe."""
        repo = InMemoryCategoryRepository()
        result = repo.find_by_slug("non-existent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    def test_find_all(self) -> None:
        """find_all debe retornar todas las categorías."""
        repo = InMemoryCategoryRepository()
        repo.save(make_category(name="Tech", slug="tech"))
        repo.save(make_category(name="Science", slug="science"))
        assert len(repo.find_all()) == 2

    def test_find_active(self) -> None:
        """find_active debe retornar solo categorías activas."""
        repo = InMemoryCategoryRepository()
        repo.save(make_category(name="Active1", slug="a1", is_active=True))
        repo.save(make_category(name="Active2", slug="a2", is_active=True))
        repo.save(
            make_category(name="Inactive", slug="inact", is_active=False)
        )
        actives = repo.find_active()
        assert len(actives) == 2
        assert all(c.is_active for c in actives)

    def test_find_by_parent(self) -> None:
        """find_by_parent retorna subcategorías directas."""
        repo = InMemoryCategoryRepository()
        parent = make_category(name="Parent", slug="parent")
        repo.save(parent)
        child1 = make_category(
            name="Child1", slug="child1", parent_id=parent.id
        )
        repo.save(child1)
        child2 = make_category(
            name="Child2", slug="child2", parent_id=parent.id
        )
        repo.save(child2)
        # Unrelated (no parent)
        repo.save(make_category(name="Other", slug="other"))

        children = repo.find_by_parent(parent.id)
        assert len(children) == 2

    def test_exists_by_slug(self) -> None:
        """exists_by_slug retorna True si existe."""
        repo = InMemoryCategoryRepository()
        repo.save(make_category(name="Tech", slug="tech"))
        assert repo.exists_by_slug("tech") is True
        assert repo.exists_by_slug("non-existent") is False


# ═══════════════════════════════════════════════════
# InMemoryTopicRepository Tests
# ═══════════════════════════════════════════════════


class TestInMemoryTopicRepository:
    """Test suite for InMemoryTopicRepository."""

    def test_save_and_find_by_id(self) -> None:
        """save + find_by_id debe retornar el mismo topic."""
        repo = InMemoryTopicRepository()
        topic = make_topic(name="AI")
        repo.save(topic)

        result = repo.find_by_id(topic.id)
        assert result.is_success
        assert result.value.name == "AI"

    def test_find_by_id_not_found(self) -> None:
        """find_by_id debe retornar Failure si no existe."""
        repo = InMemoryTopicRepository()
        result = repo.find_by_id(TopicId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    def test_find_by_name(self) -> None:
        """find_by_name debe retornar topic por nombre."""
        repo = InMemoryTopicRepository()
        repo.save(make_topic(name="Machine Learning"))
        result = repo.find_by_name("Machine Learning")
        assert result.is_success
        assert result.value.name == "Machine Learning"

    def test_find_by_name_not_found(self) -> None:
        """find_by_name debe retornar Failure si no existe."""
        repo = InMemoryTopicRepository()
        result = repo.find_by_name("NonExistent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    def test_find_all(self) -> None:
        """find_all debe retornar todos los topics."""
        repo = InMemoryTopicRepository()
        repo.save(make_topic(name="AI"))
        repo.save(make_topic(name="Blockchain"))
        assert len(repo.find_all()) == 2

    def test_find_active(self) -> None:
        """find_active retorna solo topics activos."""
        repo = InMemoryTopicRepository()
        repo.save(make_topic(name="Active1", is_active=True))
        repo.save(make_topic(name="Active2", is_active=True))
        repo.save(make_topic(name="Inactive", is_active=False))
        actives = repo.find_active()
        assert len(actives) == 2
        assert all(t.is_active for t in actives)

    def test_exists_by_name(self) -> None:
        """exists_by_name retorna True si existe."""
        repo = InMemoryTopicRepository()
        repo.save(make_topic(name="AI"))
        assert repo.exists_by_name("AI") is True
        assert repo.exists_by_name("NonExistent") is False
