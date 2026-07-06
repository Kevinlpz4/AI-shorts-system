"""
Contract Tests — Repository Contract Parity (InMemory ↔ SQLAlchemy).

Cada escenario se ejecuta con ambas implementaciones para demostrar que
cumplen el mismo contrato.

Estructura:
    - Fixtures parametrizadas que retornan (repo_impl_name, repo_instance)
    - Tests genéricos que usan la fixture
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from foundation.result.result import Failure, Success

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
from ingestion.infrastructure.persistence import PersistenceBase
from ingestion.infrastructure.persistence.exceptions import DuplicateEntityError
from ingestion.infrastructure.persistence.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyFeedRepository,
    SQLAlchemyNewsSourceRepository,
    SQLAlchemyRawArticleRepository,
    SQLAlchemyTopicRepository,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures — Repository pairs
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sqlite_session():
    """Create a fresh SQLite in-memory database + session per test."""
    engine = create_engine("sqlite:///:memory:")
    PersistenceBase.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine)()
    yield test_session
    test_session.close()
    engine.dispose()


# ── NewsSource ────────────────────────────────────────────────────────────────


@pytest.fixture(params=[
    pytest.param("inmemory", id="inmemory"),
    pytest.param("sqlalchemy", id="sqlalchemy"),
])
def news_source_repo(request, sqlite_session):
    """Parametrized fixture: retorna NewsSourceRepository (ambas impls)."""
    if request.param == "inmemory":
        return InMemoryNewsSourceRepository()
    return SQLAlchemyNewsSourceRepository(sqlite_session)


@pytest.fixture(params=[
    pytest.param("inmemory", id="inmemory"),
    pytest.param("sqlalchemy", id="sqlalchemy"),
])
def feed_repo(request, sqlite_session):
    """Parametrized fixture: retorna FeedRepository (ambas impls)."""
    if request.param == "inmemory":
        return InMemoryFeedRepository()
    return SQLAlchemyFeedRepository(sqlite_session)


@pytest.fixture(params=[
    pytest.param("inmemory", id="inmemory"),
    pytest.param("sqlalchemy", id="sqlalchemy"),
])
def raw_article_repo(request, sqlite_session):
    """Parametrized fixture: retorna RawArticleRepository (ambas impls)."""
    if request.param == "inmemory":
        return InMemoryRawArticleRepository()
    return SQLAlchemyRawArticleRepository(sqlite_session)


@pytest.fixture(params=[
    pytest.param("inmemory", id="inmemory"),
    pytest.param("sqlalchemy", id="sqlalchemy"),
])
def category_repo(request, sqlite_session):
    """Parametrized fixture: retorna CategoryRepository (ambas impls)."""
    if request.param == "inmemory":
        return InMemoryCategoryRepository()
    return SQLAlchemyCategoryRepository(sqlite_session)


@pytest.fixture(params=[
    pytest.param("inmemory", id="inmemory"),
    pytest.param("sqlalchemy", id="sqlalchemy"),
])
def topic_repo(request, sqlite_session):
    """Parametrized fixture: retorna TopicRepository (ambas impls)."""
    if request.param == "inmemory":
        return InMemoryTopicRepository()
    return SQLAlchemyTopicRepository(sqlite_session)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


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
    url: str | None = None,
    label: str = "Test Feed",
    is_active: bool = True,
) -> Feed:
    global _feed_counter
    _feed_counter += 1
    feed_url = url or f"https://example.com/feed-{_feed_counter}"
    return Feed(
        id=FeedId.generate(),
        source_id=source_id or SourceId.generate(),
        url=ArticleUrl(feed_url),
        label=ArticleTitle(label),
        language=Language("en"),
        is_active=is_active,
        sync_policy=SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
        ),
    )


_article_counter: int = 0
_feed_counter: int = 0


def make_article(
    feed_id: FeedId | None = None,
    external_id: str | None = None,
    content_hash: str | None = None,
    title: str = "Test Article",
    url: str | None = None,
) -> RawArticle:
    global _article_counter
    _article_counter += 1
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


# ══════════════════════════════════════════════════════════════════════════════
# NewsSourceRepository Contract Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestNewsSourceRepositoryContract:
    """Contract: NewsSourceRepository — InMemory y SQLAlchemy."""

    def test_save_and_find_by_id(self, news_source_repo):
        """save + find_by_id debe retornar el mismo source."""
        source = make_source(name="Reddit")
        news_source_repo.save(source)

        result = news_source_repo.find_by_id(source.id)
        assert result.is_success
        assert result.value.name == "Reddit"
        assert result.value.is_active is True

    def test_find_by_id_not_found(self, news_source_repo):
        """find_by_id debe retornar Failure si no existe."""
        result = news_source_repo.find_by_id(SourceId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_find_by_name(self, news_source_repo):
        """find_by_name debe retornar el source por nombre."""
        source = make_source(name="UniqueName")
        news_source_repo.save(source)

        result = news_source_repo.find_by_name("UniqueName")
        assert result.is_success
        assert result.value.name == "UniqueName"

    def test_find_by_name_not_found(self, news_source_repo):
        """find_by_name debe retornar Failure si no existe."""
        result = news_source_repo.find_by_name("NonExistent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_exists_by_name(self, news_source_repo):
        """exists_by_name debe retornar True si existe."""
        news_source_repo.save(make_source(name="Existing"))
        assert news_source_repo.exists_by_name("Existing") is True
        assert news_source_repo.exists_by_name("NonExistent") is False

    def test_find_all(self, news_source_repo):
        """find_all debe retornar todos los sources."""
        news_source_repo.save(make_source(name="A"))
        news_source_repo.save(make_source(name="B"))
        assert len(news_source_repo.find_all()) == 2

    def test_find_active(self, news_source_repo):
        """find_active debe retornar solo los activos."""
        news_source_repo.save(make_source(name="Active1", is_active=True))
        news_source_repo.save(make_source(name="Active2", is_active=True))
        news_source_repo.save(make_source(name="Inactive", is_active=False))
        actives = news_source_repo.find_active()
        assert len(actives) == 2
        assert all(s.is_active for s in actives)

    def test_save_update(self, news_source_repo):
        """save con ID existente debe actualizar, no crear duplicado."""
        source = make_source(name="Original")
        news_source_repo.save(source)

        source.name = "Updated"
        news_source_repo.save(source)

        result = news_source_repo.find_by_id(source.id)
        assert result.is_success
        assert result.value.name == "Updated"

    def test_duplicate_name_raises_error(self, news_source_repo):
        """save con name duplicado debe lanzar DuplicateEntityError."""
        news_source_repo.save(make_source(name="Unique"))
        with pytest.raises(DuplicateEntityError):
            news_source_repo.save(make_source(name="Unique"))


# ══════════════════════════════════════════════════════════════════════════════
# FeedRepository Contract Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestFeedRepositoryContract:
    """Contract: FeedRepository — InMemory y SQLAlchemy."""

    def test_save_and_find_by_id(self, feed_repo):
        """save + find_by_id debe retornar el mismo feed."""
        feed = make_feed(label="My Feed")
        feed_repo.save(feed)

        result = feed_repo.find_by_id(feed.id)
        assert result.is_success
        assert result.value.label.value == "My Feed"

    def test_find_by_id_not_found(self, feed_repo):
        """find_by_id debe retornar Failure si no existe."""
        result = feed_repo.find_by_id(FeedId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND

    def test_find_by_source(self, feed_repo):
        """find_by_source debe retornar feeds de un source."""
        sid = SourceId.generate()
        feed_repo.save(make_feed(source_id=sid, label="Feed1"))
        feed_repo.save(make_feed(source_id=sid, label="Feed2"))
        other_sid = SourceId.generate()
        feed_repo.save(make_feed(source_id=other_sid, label="Other"))

        feeds = feed_repo.find_by_source(sid)
        assert len(feeds) == 2

    def test_find_by_url(self, feed_repo):
        """find_by_url debe retornar el feed por URL dentro del source."""
        sid = SourceId.generate()
        feed = make_feed(
            source_id=sid,
            url="https://example.com/rss",
            label="Found",
        )
        feed_repo.save(feed)

        result = feed_repo.find_by_url(sid, ArticleUrl("https://example.com/rss"))
        assert result.is_success
        assert result.value.label.value == "Found"

    def test_find_by_url_not_found(self, feed_repo):
        """find_by_url debe retornar Failure si no existe."""
        sid = SourceId.generate()
        result = feed_repo.find_by_url(sid, ArticleUrl("https://example.com/rss"))
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND

    def test_find_active_by_source(self, feed_repo):
        """find_active_by_source debe retornar solo feeds activos."""
        sid = SourceId.generate()
        feed_repo.save(make_feed(source_id=sid, label="Active1", is_active=True))
        feed_repo.save(make_feed(source_id=sid, label="Active2", is_active=True))
        feed_repo.save(make_feed(source_id=sid, label="Inactive", is_active=False))

        actives = feed_repo.find_active_by_source(sid)
        assert len(actives) == 2
        assert all(f.is_active for f in actives)

    def test_exists_by_source_and_url(self, feed_repo):
        """exists_by_source_and_url retorna True si existe."""
        sid = SourceId.generate()
        feed_repo.save(make_feed(source_id=sid, url="https://example.com/rss"))
        assert (
            feed_repo.exists_by_source_and_url(
                sid, ArticleUrl("https://example.com/rss"),
            )
            is True
        )
        assert (
            feed_repo.exists_by_source_and_url(
                sid, ArticleUrl("https://other.com/rss"),
            )
            is False
        )

    def test_count_active_by_source(self, feed_repo):
        """count_active_by_source retorna conteo correcto."""
        sid = SourceId.generate()
        feed_repo.save(make_feed(source_id=sid, is_active=True))
        feed_repo.save(make_feed(source_id=sid, is_active=True))
        feed_repo.save(make_feed(source_id=sid, is_active=False))
        assert feed_repo.count_active_by_source(sid) == 2
        assert feed_repo.count_active_by_source(SourceId.generate()) == 0

    def test_save_update(self, feed_repo):
        """save con ID existente debe actualizar, no crear duplicado."""
        feed = make_feed(label="Original")
        feed_repo.save(feed)

        feed.label = ArticleTitle("Updated")
        feed_repo.save(feed)

        result = feed_repo.find_by_id(feed.id)
        assert result.is_success
        assert result.value.label.value == "Updated"

    def test_duplicate_source_url_raises_error(self, feed_repo):
        """save con source_id+url duplicado debe lanzar DuplicateEntityError."""
        sid = SourceId.generate()
        feed_repo.save(
            make_feed(source_id=sid, url="https://example.com/dup"),
        )
        with pytest.raises(DuplicateEntityError):
            feed_repo.save(
                make_feed(source_id=sid, url="https://example.com/dup"),
            )


# ══════════════════════════════════════════════════════════════════════════════
# RawArticleRepository Contract Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestRawArticleRepositoryContract:
    """Contract: RawArticleRepository — InMemory y SQLAlchemy."""

    def test_save_and_find_by_id(self, raw_article_repo):
        """save + find_by_id debe retornar el mismo artículo."""
        fid = FeedId.generate()
        article = make_article(feed_id=fid, external_id="ext-1")
        raw_article_repo.save(article)

        result = raw_article_repo.find_by_id(article.id)
        assert result.is_success
        assert result.value.external_id == "ext-1"
        assert result.value.feed_id == fid

    def test_find_by_id_not_found(self, raw_article_repo):
        """find_by_id debe retornar Failure si no existe."""
        result = raw_article_repo.find_by_id(RawArticleId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.RAW_ARTICLE_NOT_FOUND

    def test_find_by_feed(self, raw_article_repo):
        """find_by_feed debe retornar artículos de un feed."""
        fid = FeedId.generate()
        raw_article_repo.save(make_article(feed_id=fid, external_id="ext-1"))
        raw_article_repo.save(make_article(feed_id=fid, external_id="ext-2"))
        other_fid = FeedId.generate()
        raw_article_repo.save(make_article(feed_id=other_fid, external_id="ext-3"))

        articles = raw_article_repo.find_by_feed(fid)
        assert len(articles) == 2

    def test_find_by_feed_pagination(self, raw_article_repo):
        """find_by_feed debe paginar correctamente."""
        fid = FeedId.generate()
        for i in range(10):
            raw_article_repo.save(
                make_article(
                    feed_id=fid,
                    external_id=f"ext-{i}",
                    content_hash=f"{i:01x}{'a' * 63}",
                ),
            )

        page1 = raw_article_repo.find_by_feed(fid, page=1, size=3)
        page2 = raw_article_repo.find_by_feed(fid, page=2, size=3)
        assert len(page1) == 3
        assert len(page2) == 3
        assert page1[0].external_id != page2[0].external_id

    def test_find_by_hash(self, raw_article_repo):
        """find_by_hash debe retornar artículo por hash."""
        fid = FeedId.generate()
        article = make_article(
            feed_id=fid,
            external_id="ext-1",
            content_hash="b" * 64,
        )
        raw_article_repo.save(article)

        result = raw_article_repo.find_by_hash(fid, "b" * 64)
        assert result.is_success
        assert result.value.external_id == "ext-1"

    def test_find_by_hash_not_found(self, raw_article_repo):
        """find_by_hash debe retornar Failure si no existe."""
        fid = FeedId.generate()
        result = raw_article_repo.find_by_hash(fid, "c" * 64)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.RAW_ARTICLE_NOT_FOUND

    def test_exists_by_url(self, raw_article_repo):
        """exists_by_url debe retornar True si existe."""
        fid = FeedId.generate()
        raw_article_repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                url="https://example.com/article1",
            ),
        )
        assert (
            raw_article_repo.exists_by_url(
                fid, ArticleUrl("https://example.com/article1"),
            )
            is True
        )
        assert (
            raw_article_repo.exists_by_url(
                fid, ArticleUrl("https://other.com/article"),
            )
            is False
        )

    def test_exists_by_hash(self, raw_article_repo):
        """exists_by_hash debe retornar True si existe."""
        fid = FeedId.generate()
        raw_article_repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="d" * 64,
            ),
        )
        assert raw_article_repo.exists_by_hash(fid, "d" * 64) is True
        assert raw_article_repo.exists_by_hash(fid, "e" * 64) is False

    def test_count_by_feed(self, raw_article_repo):
        """count_by_feed retorna conteo correcto."""
        fid = FeedId.generate()
        raw_article_repo.save(make_article(feed_id=fid, external_id="ext-1"))
        raw_article_repo.save(make_article(feed_id=fid, external_id="ext-2"))
        assert raw_article_repo.count_by_feed(fid) == 2
        assert raw_article_repo.count_by_feed(FeedId.generate()) == 0

    def test_duplicate_external_id_raises_error(self, raw_article_repo):
        """save debe lanzar DuplicateEntityError si external_id+feed_id duplicado."""
        fid = FeedId.generate()
        raw_article_repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="a" * 64,
                url="https://example.com/article-a",
            ),
        )
        with pytest.raises(DuplicateEntityError) as excinfo:
            raw_article_repo.save(
                make_article(
                    feed_id=fid,
                    external_id="ext-1",
                    content_hash="b" * 64,
                    url="https://example.com/article-b",
                ),
            )
        assert "RawArticle" in str(excinfo.value)

    def test_duplicate_content_hash_raises_error(self, raw_article_repo):
        """save debe lanzar DuplicateEntityError si content_hash+feed_id duplicado."""
        fid = FeedId.generate()
        raw_article_repo.save(
            make_article(
                feed_id=fid,
                external_id="ext-1",
                content_hash="c" * 64,
                url="https://example.com/article-c",
            ),
        )
        with pytest.raises(DuplicateEntityError) as excinfo:
            raw_article_repo.save(
                make_article(
                    feed_id=fid,
                    external_id="ext-2",
                    content_hash="c" * 64,
                    url="https://example.com/article-d",
                ),
            )
        assert "RawArticle" in str(excinfo.value)

    def test_save_batch(self, raw_article_repo):
        """save_batch debe guardar múltiples artículos."""
        fid = FeedId.generate()
        articles = [
            make_article(
                feed_id=fid,
                external_id=f"ext-{i}",
                content_hash=f"{i:02x}{'a' * 62}",
            )
            for i in range(5)
        ]
        raw_article_repo.save_batch(articles)
        assert raw_article_repo.count_by_feed(fid) == 5

    def test_save_batch_with_duplicate_raises_error(self, raw_article_repo):
        """save_batch con external_id duplicado debe lanzar DuplicateEntityError."""
        fid = FeedId.generate()
        raw_article_repo.save(
            make_article(feed_id=fid, external_id="existing"),
        )
        batch = [
            make_article(feed_id=fid, external_id="new-1"),
            make_article(feed_id=fid, external_id="existing"),
        ]
        with pytest.raises(DuplicateEntityError):
            raw_article_repo.save_batch(batch)


# ══════════════════════════════════════════════════════════════════════════════
# CategoryRepository Contract Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCategoryRepositoryContract:
    """Contract: CategoryRepository — InMemory y SQLAlchemy."""

    def test_save_and_find_by_id(self, category_repo):
        """save + find_by_id debe retornar la misma categoría."""
        cat = make_category(name="Tech", slug="tech")
        category_repo.save(cat)

        result = category_repo.find_by_id(cat.id)
        assert result.is_success
        assert result.value.name.value == "Tech"
        assert result.value.slug == "tech"

    def test_find_by_id_not_found(self, category_repo):
        """find_by_id debe retornar Failure si no existe."""
        result = category_repo.find_by_id(CategoryId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    def test_find_by_slug(self, category_repo):
        """find_by_slug debe retornar categoría por slug."""
        category_repo.save(make_category(name="Tech", slug="tech"))
        result = category_repo.find_by_slug("tech")
        assert result.is_success
        assert result.value.slug == "tech"

    def test_find_by_slug_not_found(self, category_repo):
        """find_by_slug debe retornar Failure si no existe."""
        result = category_repo.find_by_slug("non-existent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    def test_find_all(self, category_repo):
        """find_all debe retornar todas las categorías."""
        category_repo.save(make_category(name="Tech", slug="tech"))
        category_repo.save(make_category(name="Science", slug="science"))
        assert len(category_repo.find_all()) == 2

    def test_find_active(self, category_repo):
        """find_active debe retornar solo categorías activas."""
        category_repo.save(make_category(name="Active1", slug="a1", is_active=True))
        category_repo.save(make_category(name="Active2", slug="a2", is_active=True))
        category_repo.save(
            make_category(name="Inactive", slug="inact", is_active=False),
        )
        actives = category_repo.find_active()
        assert len(actives) == 2
        assert all(c.is_active for c in actives)

    def test_find_by_parent(self, category_repo):
        """find_by_parent retorna subcategorías directas."""
        parent = make_category(name="Parent", slug="parent")
        category_repo.save(parent)
        child1 = make_category(
            name="Child1", slug="child1", parent_id=parent.id,
        )
        category_repo.save(child1)
        child2 = make_category(
            name="Child2", slug="child2", parent_id=parent.id,
        )
        category_repo.save(child2)
        category_repo.save(make_category(name="Other", slug="other"))

        children = category_repo.find_by_parent(parent.id)
        assert len(children) == 2

    def test_exists_by_slug(self, category_repo):
        """exists_by_slug retorna True si existe."""
        category_repo.save(make_category(name="Tech", slug="tech"))
        assert category_repo.exists_by_slug("tech") is True
        assert category_repo.exists_by_slug("non-existent") is False

    def test_save_update(self, category_repo):
        """save con ID existente debe actualizar, no crear duplicado."""
        cat = make_category(name="Tech", slug="tech")
        category_repo.save(cat)

        cat.name = CategoryName("Technology")
        category_repo.save(cat)

        result = category_repo.find_by_id(cat.id)
        assert result.is_success
        assert result.value.name.value == "Technology"

    def test_duplicate_slug_raises_error(self, category_repo):
        """save con slug duplicado debe lanzar DuplicateEntityError."""
        category_repo.save(make_category(name="First", slug="dup-slug"))
        with pytest.raises(DuplicateEntityError):
            category_repo.save(make_category(name="Second", slug="dup-slug"))


# ══════════════════════════════════════════════════════════════════════════════
# TopicRepository Contract Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestTopicRepositoryContract:
    """Contract: TopicRepository — InMemory y SQLAlchemy."""

    def test_save_and_find_by_id(self, topic_repo):
        """save + find_by_id debe retornar el mismo topic."""
        topic = make_topic(name="AI")
        topic_repo.save(topic)

        result = topic_repo.find_by_id(topic.id)
        assert result.is_success
        assert result.value.name == "AI"

    def test_find_by_id_not_found(self, topic_repo):
        """find_by_id debe retornar Failure si no existe."""
        result = topic_repo.find_by_id(TopicId.generate())
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    def test_find_by_name(self, topic_repo):
        """find_by_name debe retornar topic por nombre."""
        topic_repo.save(make_topic(name="Machine Learning"))
        result = topic_repo.find_by_name("Machine Learning")
        assert result.is_success
        assert result.value.name == "Machine Learning"

    def test_find_by_name_not_found(self, topic_repo):
        """find_by_name debe retornar Failure si no existe."""
        result = topic_repo.find_by_name("NonExistent")
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    def test_find_all(self, topic_repo):
        """find_all debe retornar todos los topics."""
        topic_repo.save(make_topic(name="AI"))
        topic_repo.save(make_topic(name="Blockchain"))
        assert len(topic_repo.find_all()) == 2

    def test_find_active(self, topic_repo):
        """find_active retorna solo topics activos."""
        topic_repo.save(make_topic(name="Active1", is_active=True))
        topic_repo.save(make_topic(name="Active2", is_active=True))
        topic_repo.save(make_topic(name="Inactive", is_active=False))
        actives = topic_repo.find_active()
        assert len(actives) == 2
        assert all(t.is_active for t in actives)

    def test_exists_by_name(self, topic_repo):
        """exists_by_name retorna True si existe."""
        topic_repo.save(make_topic(name="AI"))
        assert topic_repo.exists_by_name("AI") is True
        assert topic_repo.exists_by_name("NonExistent") is False

    def test_save_update(self, topic_repo):
        """save con ID existente debe actualizar, no crear duplicado."""
        topic = make_topic(name="Original")
        topic_repo.save(topic)

        topic.name = "Updated"
        topic_repo.save(topic)

        result = topic_repo.find_by_id(topic.id)
        assert result.is_success
        assert result.value.name == "Updated"

    def test_duplicate_name_raises_error(self, topic_repo):
        """save con name duplicado debe lanzar DuplicateEntityError."""
        topic_repo.save(make_topic(name="Unique"))
        with pytest.raises(DuplicateEntityError):
            topic_repo.save(make_topic(name="Unique"))
