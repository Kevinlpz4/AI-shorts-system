"""
Roundtrip tests for ORM Models (Sprint 5.2).

Tests cover:
  - Each model: create → save → load → assert
  - SyncPolicy composite mapping on Feed
  - Self-referencing parent relationship on Category
  - 1:N relationship: NewsSource → Feeds
  - M:N relationships (categories, topics) with eager loading
  - Optimistic locking (version column)
  - Constraints (FK violations)
  - RawArticle immutability characteristics (no version, no updated_at)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from ingestion.infrastructure.persistence import PersistenceBase
from ingestion.infrastructure.persistence.models import (
    CategoryModel,
    FeedModel,
    NewsSourceModel,
    RawArticleModel,
    TopicModel,
    feed_category_table,
    feed_topic_table,
    news_source_category_table,
    news_source_topic_table,
)

from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    RawArticleId,
    SourceId,
    TopicId,
)
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy

# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def unique_uuid() -> SourceId:
    """Generate a unique SourceId for each test."""
    return SourceId(value=uuid4())


# ══════════════════════════════════════════════════════════════════════════════
# NewsSourceModel Roundtrip
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestNewsSourceModel:
    """Roundtrip tests for NewsSourceModel."""

    def test_create_and_load(self, engine, engine_session):
        """Crear un NewsSourceModel, persistirlo y leerlo debe preservar todos los campos."""
        src_id = SourceId(value=uuid4())
        model = NewsSourceModel(
            id=src_id,
            name="Test Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com/rss"),
            is_active=True,
            version=1,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(NewsSourceModel, src_id)
        assert loaded is not None
        assert loaded.id == src_id
        assert type(loaded.id) is SourceId
        assert loaded.name == "Test Source"
        assert loaded.source_type is SourceType.RSS
        assert isinstance(loaded.source_url, SourceUrl)
        assert loaded.source_url.value == "https://example.com/rss"
        assert loaded.is_active is True
        assert loaded.version == 1

    def test_load_inactive_source(self, engine, engine_session):
        """is_active=False debe persistir correctamente."""
        src_id = SourceId(value=uuid4())
        model = NewsSourceModel(
            id=src_id,
            name="Inactive Source",
            source_type=SourceType.API,
            source_url=SourceUrl("https://api.example.com"),
            is_active=False,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(NewsSourceModel, src_id)
        assert loaded is not None
        assert loaded.is_active is False

    def test_unique_name_constraint(self, engine, engine_session):
        """Dos sources con el mismo name deben violar UNIQUE constraint."""
        src_id_1 = SourceId(value=uuid4())
        src_id_2 = SourceId(value=uuid4())

        engine_session.add(NewsSourceModel(
            id=src_id_1,
            name="Duplicate Name",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com/1"),
        ))
        engine_session.commit()

        engine_session.add(NewsSourceModel(
            id=src_id_2,
            name="Duplicate Name",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com/2"),
        ))

        with pytest.raises(IntegrityError):
            engine_session.commit()

    def test_version_increments_on_update(self, engine, engine_session):
        """La columna version debe incrementarse al modificar el registro."""
        src_id = SourceId(value=uuid4())
        engine_session.add(NewsSourceModel(
            id=src_id,
            name="Version Test",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        ))
        engine_session.commit()

        loaded = engine_session.get(NewsSourceModel, src_id)
        assert loaded.version == 1

        # Modificar y guardar
        loaded.name = "Updated Name"
        engine_session.commit()

        # Recargar y verificar que version aumentó
        engine_session.expire_all()
        reloaded = engine_session.get(NewsSourceModel, src_id)
        assert reloaded.version == 2


# ══════════════════════════════════════════════════════════════════════════════
# FeedModel Roundtrip (including SyncPolicy composite)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestFeedModel:
    """Roundtrip tests for FeedModel, including SyncPolicy composite."""

    @pytest.fixture
    def source(self, engine_session):
        """Create a parent NewsSource for feed tests."""
        src = NewsSourceModel(
            id=SourceId(value=uuid4()),
            name="Feed Test Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(src)
        engine_session.commit()
        return src

    def test_create_and_load(self, engine, engine_session, source):
        """FeedModel con SyncPolicy compuesto debe persistir y reconstruirse."""
        feed_id = FeedId(value=uuid4())
        policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=30,
            max_retries=5,
            backoff_multiplier=3.0,
            max_backoff_minutes=120,
            timeout_seconds=60,
            max_items_per_run=200,
        )
        model = FeedModel(
            id=feed_id,
            source_id=source.id,
            url=ArticleUrl("https://example.com/feed.xml"),
            label=ArticleTitle("Test Feed"),
            language=Language("en"),
            is_active=True,
            sync_mode=policy.mode,
            interval_minutes=policy.interval_minutes,
            max_retries=policy.max_retries,
            backoff_multiplier=policy.backoff_multiplier,
            max_backoff_minutes=policy.max_backoff_minutes,
            timeout_seconds=policy.timeout_seconds,
            max_items_per_run=policy.max_items_per_run,
            retry_count=0,
            version=1,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(FeedModel, feed_id)
        assert loaded is not None
        assert type(loaded.id) is FeedId
        assert type(loaded.source_id) is SourceId
        assert loaded.source_id == source.id
        assert isinstance(loaded.url, ArticleUrl)
        assert loaded.label.value == "Test Feed"
        assert loaded.language.code == "en"
        assert loaded.retry_count == 0

        # SyncPolicy composite
        assert isinstance(loaded.sync_policy, SyncPolicy)
        assert loaded.sync_policy.mode is SyncMode.PULL
        assert loaded.sync_policy.interval_minutes == 30
        assert loaded.sync_policy.max_retries == 5
        assert loaded.sync_policy.backoff_multiplier == 3.0
        assert loaded.sync_policy.max_backoff_minutes == 120
        assert loaded.sync_policy.timeout_seconds == 60
        assert loaded.sync_policy.max_items_per_run == 200

    def test_sync_policy_default_values(self, engine, engine_session, source):
        """SyncPolicy debe reconstruirse con valores por defecto (incluyendo PULL+interval)."""
        feed_id = FeedId(value=uuid4())
        model = FeedModel(
            id=feed_id,
            source_id=source.id,
            url=ArticleUrl("https://example.com/feed2.xml"),
            label=ArticleTitle("Default Policy Feed"),
            language=Language("es"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,  # PULL requires interval_minutes per domain VO
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(FeedModel, feed_id)
        assert loaded.sync_policy.mode is SyncMode.PULL
        assert loaded.sync_policy.interval_minutes == 30
        assert loaded.sync_policy.max_retries == 3
        assert loaded.sync_policy.backoff_multiplier == 2.0
        assert loaded.sync_policy.max_backoff_minutes == 60
        assert loaded.sync_policy.timeout_seconds == 30
        assert loaded.sync_policy.max_items_per_run == 100

    def test_feed_source_relationship(self, engine, engine_session, source):
        """La relación N:1 Feed → Source debe cargarse con joined load."""
        feed_id = FeedId(value=uuid4())
        model = FeedModel(
            id=feed_id,
            source_id=source.id,
            url=ArticleUrl("https://example.com/feed3.xml"),
            label=ArticleTitle("Rel Test"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(FeedModel, feed_id)
        assert loaded.source is not None
        assert loaded.source.id == source.id
        assert loaded.source.name == "Feed Test Source"

    def test_source_feeds_relationship(self, engine, engine_session, source):
        """La relación 1:N Source → Feeds debe cargarse con lazy select."""
        feed_id = FeedId(value=uuid4())
        engine_session.add(FeedModel(
            id=feed_id,
            source_id=source.id,
            url=ArticleUrl("https://example.com/feed4.xml"),
            label=ArticleTitle("Child Feed"),
            language=Language("fr"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        ))
        engine_session.commit()

        loaded_source = engine_session.get(NewsSourceModel, source.id)
        # La relación feeds es lazy — debe cargarse al acceder
        feeds = loaded_source.feeds
        assert len(feeds) == 1
        assert feeds[0].id == feed_id

    def test_interval_minutes_nullable_for_push(self, engine, engine_session, source):
        """interval_minutes debe poder ser NULL para modos no-PULL."""
        feed_id = FeedId(value=uuid4())
        model = FeedModel(
            id=feed_id,
            source_id=source.id,
            url=ArticleUrl("https://example.com/push-feed"),
            label=ArticleTitle("Push Feed"),
            language=Language("en"),
            sync_mode=SyncMode.PUSH,
            interval_minutes=None,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(FeedModel, feed_id)
        assert loaded.interval_minutes is None
        assert loaded.sync_policy.mode is SyncMode.PUSH
        assert loaded.sync_policy.interval_minutes is None


# ══════════════════════════════════════════════════════════════════════════════
# RawArticleModel Roundtrip
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestRawArticleModel:
    """Roundtrip tests for RawArticleModel (immutable entity)."""

    @pytest.fixture
    def source_and_feed(self, engine_session):
        """Create a source+feed for raw article tests."""
        src = NewsSourceModel(
            id=SourceId(value=uuid4()),
            name="Article Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(src)
        engine_session.flush()

        feed = FeedModel(
            id=FeedId(value=uuid4()),
            source_id=src.id,
            url=ArticleUrl("https://example.com/feed.xml"),
            label=ArticleTitle("Article Feed"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(feed)
        engine_session.commit()
        return src, feed

    def test_create_and_load(self, engine, engine_session, source_and_feed):
        """RawArticleModel debe persistir y reconstruir todos los campos."""
        _, feed = source_and_feed
        now = datetime.now(timezone.utc)
        pub_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        article_id = RawArticleId(value=uuid4())

        model = RawArticleModel(
            id=article_id,
            feed_id=feed.id,
            external_id="ext-001",
            content_hash="a" * 64,
            title=ArticleTitle("Test Article"),
            url=ArticleUrl("https://example.com/article/1"),
            author="Test Author",
            language=Language("en"),
            published_at=pub_at,
            fetched_at=now,
            content_preview="This is a preview...",
            provider_metadata={"key": "value", "count": 42},
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(RawArticleModel, article_id)
        assert loaded is not None
        assert type(loaded.id) is RawArticleId
        assert type(loaded.feed_id) is FeedId
        assert loaded.feed_id == feed.id
        assert loaded.external_id == "ext-001"
        assert loaded.content_hash == "a" * 64
        assert isinstance(loaded.title, ArticleTitle)
        assert loaded.title.value == "Test Article"
        assert isinstance(loaded.url, ArticleUrl)
        assert loaded.url.value == "https://example.com/article/1"
        assert loaded.author == "Test Author"
        assert isinstance(loaded.language, Language)
        assert loaded.language.code == "en"
        # SQLite does not preserve tzinfo — compare naive UTC values
        assert loaded.published_at.replace(tzinfo=None) == pub_at.replace(tzinfo=None)
        assert loaded.fetched_at.replace(tzinfo=None) == now.replace(tzinfo=None)
        assert loaded.content_preview == "This is a preview..."
        assert loaded.provider_metadata == {"key": "value", "count": 42}

    def test_nullable_fields(self, engine, engine_session, source_and_feed):
        """Campos opcionales deben poder ser None."""
        _, feed = source_and_feed
        article_id = RawArticleId(value=uuid4())

        model = RawArticleModel(
            id=article_id,
            feed_id=feed.id,
            external_id="ext-002",
            content_hash="b" * 64,
            title=ArticleTitle("Minimal Article"),
            url=ArticleUrl("https://example.com/article/2"),
            fetched_at=datetime.now(timezone.utc),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(RawArticleModel, article_id)
        assert loaded.author is None
        assert loaded.language is None
        assert loaded.published_at is None
        assert loaded.content_preview is None
        assert loaded.provider_metadata == {}

    def test_no_version_column(self):
        """RawArticleModel NO debe tener columna version (inmutable)."""
        assert not hasattr(RawArticleModel, "version")

    def test_no_updated_at_column(self):
        """RawArticleModel NO debe tener columna updated_at (inmutable)."""
        assert not hasattr(RawArticleModel, "updated_at")


# ══════════════════════════════════════════════════════════════════════════════
# CategoryModel Roundtrip
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestCategoryModel:
    """Roundtrip tests for CategoryModel (self-referencing hierarchy)."""

    def test_create_and_load(self, engine, engine_session):
        """CategoryModel debe persistir y reconstruir todos los campos."""
        cat_id = CategoryId(value=uuid4())

        model = CategoryModel(
            id=cat_id,
            name=CategoryName("Technology"),
            slug="technology",
            description="Tech-related categories",
            is_active=True,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(CategoryModel, cat_id)
        assert loaded is not None
        assert type(loaded.id) is CategoryId
        assert isinstance(loaded.name, CategoryName)
        assert loaded.name.value == "Technology"
        assert loaded.slug == "technology"
        assert loaded.description == "Tech-related categories"
        assert loaded.is_active is True

    def test_self_referencing_parent(self, engine, engine_session):
        """La relación parent debe cargarse con joined load."""
        parent_id = CategoryId(value=uuid4())
        child_id = CategoryId(value=uuid4())

        engine_session.add(CategoryModel(
            id=parent_id,
            name=CategoryName("Root"),
            slug="root",
        ))
        engine_session.flush()

        engine_session.add(CategoryModel(
            id=child_id,
            name=CategoryName("Child"),
            slug="child",
            parent_id=parent_id,
        ))
        engine_session.commit()

        loaded = engine_session.get(CategoryModel, child_id)
        assert loaded.parent is not None
        assert loaded.parent.id == parent_id
        assert loaded.parent.name.value == "Root"

    def test_parent_can_be_null(self, engine, engine_session):
        """parent_id=None debe cargarse como parent=None."""
        cat_id = CategoryId(value=uuid4())

        model = CategoryModel(
            id=cat_id,
            name=CategoryName("Root Category"),
            slug="root-cat",
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(CategoryModel, cat_id)
        assert loaded.parent is None
        assert loaded.parent_id is None


# ══════════════════════════════════════════════════════════════════════════════
# TopicModel Roundtrip
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestTopicModel:
    """Roundtrip tests for TopicModel (simplest model)."""

    def test_create_and_load(self, engine, engine_session):
        """TopicModel debe persistir y reconstruir todos los campos."""
        topic_id = TopicId(value=uuid4())

        model = TopicModel(
            id=topic_id,
            name="AI & Machine Learning",
            description="Artificial intelligence and ML topics",
            is_active=True,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(TopicModel, topic_id)
        assert loaded is not None
        assert type(loaded.id) is TopicId
        assert loaded.name == "AI & Machine Learning"
        assert loaded.description == "Artificial intelligence and ML topics"
        assert loaded.is_active is True

    def test_unique_name_constraint(self, engine, engine_session):
        """Dos topics con el mismo name deben violar UNIQUE constraint."""
        t1_id = TopicId(value=uuid4())
        t2_id = TopicId(value=uuid4())

        engine_session.add(TopicModel(
            id=t1_id,
            name="Unique Topic",
        ))
        engine_session.commit()

        engine_session.add(TopicModel(
            id=t2_id,
            name="Unique Topic",
        ))
        with pytest.raises(IntegrityError):
            engine_session.commit()


# ══════════════════════════════════════════════════════════════════════════════
# M:N Relationship Tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestManyToManyRelationships:
    """Tests for M:N relationships via association tables."""

    @pytest.fixture
    def categories(self, engine_session):
        """Create test categories."""
        cats = []
        for name, slug in [("Tech", "tech"), ("Science", "science")]:
            cat = CategoryModel(
                id=CategoryId(value=uuid4()),
                name=CategoryName(name),
                slug=slug,
            )
            engine_session.add(cat)
            cats.append(cat)
        engine_session.commit()
        return cats

    @pytest.fixture
    def topics(self, engine_session):
        """Create test topics."""
        tops = []
        for name in ["AI", "Space"]:
            topic = TopicModel(
                id=TopicId(value=uuid4()),
                name=name,
            )
            engine_session.add(topic)
            tops.append(topic)
        engine_session.commit()
        return tops

    @pytest.fixture
    def source(self, engine_session):
        """Create a test source."""
        src = NewsSourceModel(
            id=SourceId(value=uuid4()),
            name="M:N Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(src)
        engine_session.commit()
        return src

    def test_source_categories_m2m(self, engine, engine_session, source, categories):
        """NewsSource → Categories M:N debe funcionar con selectinload."""
        # Insert association rows directly
        for cat in categories:
            engine_session.execute(
                news_source_category_table.insert().values(
                    source_id=source.id,
                    category_id=cat.id,
                )
            )
        engine_session.commit()

        # Load with explicit selectinload
        stmt = (
            select(NewsSourceModel)
            .where(NewsSourceModel.id == source.id)
            .options(selectinload(NewsSourceModel.categories))
        )
        loaded = engine_session.execute(stmt).scalar_one()
        assert len(loaded.categories) == 2
        cat_names = {c.name.value for c in loaded.categories}
        assert cat_names == {"Tech", "Science"}

    def test_source_topics_m2m(self, engine, engine_session, source, topics):
        """NewsSource → Topics M:N debe funcionar con selectinload."""
        for topic in topics:
            engine_session.execute(
                news_source_topic_table.insert().values(
                    source_id=source.id,
                    topic_id=topic.id,
                )
            )
        engine_session.commit()

        stmt = (
            select(NewsSourceModel)
            .where(NewsSourceModel.id == source.id)
            .options(selectinload(NewsSourceModel.topics))
        )
        loaded = engine_session.execute(stmt).scalar_one()
        assert len(loaded.topics) == 2
        topic_names = {t.name for t in loaded.topics}
        assert topic_names == {"AI", "Space"}

    def test_feed_categories_m2m(self, engine, engine_session, source, categories):
        """Feed → Categories M:N debe funcionar con selectinload."""
        feed = FeedModel(
            id=FeedId(value=uuid4()),
            source_id=source.id,
            url=ArticleUrl("https://example.com/m2m-feed"),
            label=ArticleTitle("M2M Feed"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(feed)
        engine_session.flush()

        for cat in categories:
            engine_session.execute(
                feed_category_table.insert().values(
                    feed_id=feed.id,
                    category_id=cat.id,
                )
            )
        engine_session.commit()

        stmt = (
            select(FeedModel)
            .where(FeedModel.id == feed.id)
            .options(selectinload(FeedModel.categories))
        )
        loaded = engine_session.execute(stmt).scalar_one()
        assert len(loaded.categories) == 2

    def test_feed_topics_m2m(self, engine, engine_session, source, topics):
        """Feed → Topics M:N debe funcionar con selectinload."""
        feed = FeedModel(
            id=FeedId(value=uuid4()),
            source_id=source.id,
            url=ArticleUrl("https://example.com/m2m-feed-2"),
            label=ArticleTitle("M2M Feed 2"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(feed)
        engine_session.flush()

        for topic in topics:
            engine_session.execute(
                feed_topic_table.insert().values(
                    feed_id=feed.id,
                    topic_id=topic.id,
                )
            )
        engine_session.commit()

        stmt = (
            select(FeedModel)
            .where(FeedModel.id == feed.id)
            .options(selectinload(FeedModel.topics))
        )
        loaded = engine_session.execute(stmt).scalar_one()
        assert len(loaded.topics) == 2


# ══════════════════════════════════════════════════════════════════════════════
# FK Constraint Tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestForeignKeyConstraints:
    """Tests for referential integrity constraints."""

    def test_feed_requires_existing_source(self, engine, engine_session):
        """Feed con source_id inexistente debe violar FK."""
        feed = FeedModel(
            id=FeedId(value=uuid4()),
            source_id=SourceId(value=uuid4()),  # Does not exist
            url=ArticleUrl("https://example.com/orphan"),
            label=ArticleTitle("Orphan Feed"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(feed)
        with pytest.raises(IntegrityError):
            engine_session.commit()

    def test_raw_article_requires_existing_feed(self, engine, engine_session):
        """RawArticle con feed_id inexistente debe violar FK."""
        article = RawArticleModel(
            id=RawArticleId(value=uuid4()),
            feed_id=FeedId(value=uuid4()),  # Does not exist
            external_id="ext-test",
            content_hash="c" * 64,
            title=ArticleTitle("Orphan Article"),
            url=ArticleUrl("https://example.com/article"),
            fetched_at=datetime.now(timezone.utc),
        )
        engine_session.add(article)
        with pytest.raises(IntegrityError):
            engine_session.commit()

    def test_category_parent_must_exist(self, engine, engine_session):
        """Category con parent_id inexistente debe violar FK."""
        cat = CategoryModel(
            id=CategoryId(value=uuid4()),
            name=CategoryName("Orphan Child"),
            slug="orphan",
            parent_id=CategoryId(value=uuid4()),  # Does not exist
        )
        engine_session.add(cat)
        with pytest.raises(IntegrityError):
            engine_session.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Aggregate Root Roundtrip (Full Domain → ORM → DB → ORM → Domain)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestFullAggregateRoundtrip:
    """Full roundtrip: construct domain entity fields → save ORM → load → assert.

    These tests simulate what a repository will do: convert domain entity
    attributes to ORM model fields, persist, load, and verify everything
    survived the roundtrip.
    """

    def test_news_source_full_roundtrip(self, engine, engine_session):
        """NewsSource completo debe sobrevivir ORM roundtrip."""
        # Simulate domain entity fields
        src_id = SourceId(value=uuid4())
        domain_fields = {
            "id": src_id,
            "name": "Full Roundtrip Source",
            "source_type": SourceType.SOCIAL_MEDIA,
            "source_url": SourceUrl("https://reddit.com/r/all"),
            "is_active": True,
        }

        model = NewsSourceModel(**domain_fields, version=1)
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(NewsSourceModel, src_id)
        for field, expected in domain_fields.items():
            actual = getattr(loaded, field)
            assert actual == expected, f"{field}: {actual!r} != {expected!r}"

    def test_feed_full_roundtrip(self, engine, engine_session):
        """Feed completo (con SyncPolicy) debe sobrevivir ORM roundtrip."""
        src = NewsSourceModel(
            id=SourceId(value=uuid4()),
            name="Feed Roundtrip Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(src)
        engine_session.flush()

        feed_id = FeedId(value=uuid4())
        policy = SyncPolicy(
            mode=SyncMode.PULL,
            interval_minutes=15,
            max_retries=3,
        )

        model = FeedModel(
            id=feed_id,
            source_id=src.id,
            url=ArticleUrl("https://example.com/feed.rss"),
            label=ArticleTitle("Full Feed"),
            language=Language("de"),
            is_active=True,
            sync_mode=policy.mode,
            interval_minutes=policy.interval_minutes,
            max_retries=policy.max_retries,
            backoff_multiplier=policy.backoff_multiplier,
            max_backoff_minutes=policy.max_backoff_minutes,
            timeout_seconds=policy.timeout_seconds,
            max_items_per_run=policy.max_items_per_run,
            retry_count=0,
            version=1,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(FeedModel, feed_id)
        assert loaded.id == feed_id
        assert loaded.source_id == src.id
        assert loaded.url == ArticleUrl("https://example.com/feed.rss")
        assert loaded.label == ArticleTitle("Full Feed")
        assert loaded.language == Language("de")
        assert loaded.sync_policy == policy
        assert loaded.retry_count == 0

    def test_raw_article_full_roundtrip(self, engine, engine_session):
        """RawArticle completo debe sobrevivir ORM roundtrip."""
        src = NewsSourceModel(
            id=SourceId(value=uuid4()),
            name="RA Source",
            source_type=SourceType.RSS,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(src)
        engine_session.flush()

        feed = FeedModel(
            id=FeedId(value=uuid4()),
            source_id=src.id,
            url=ArticleUrl("https://example.com/feed.rss"),
            label=ArticleTitle("RA Feed"),
            language=Language("en"),
            sync_mode=SyncMode.PULL,
            interval_minutes=30,
        )
        engine_session.add(feed)
        engine_session.flush()

        now = datetime.now(timezone.utc)
        article_id = RawArticleId(value=uuid4())

        model = RawArticleModel(
            id=article_id,
            feed_id=feed.id,
            external_id="roundtrip-001",
            content_hash="d" * 64,
            title=ArticleTitle("Roundtrip Article"),
            url=ArticleUrl("https://example.com/roundtrip"),
            author="Roundtrip Author",
            language=Language("fr"),
            published_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
            fetched_at=now,
            content_preview="Roundtrip preview content",
            provider_metadata={"test": True},
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(RawArticleModel, article_id)
        assert loaded.external_id == "roundtrip-001"
        assert loaded.content_hash == "d" * 64
        assert loaded.title.value == "Roundtrip Article"
        assert loaded.author == "Roundtrip Author"
        assert loaded.language.code == "fr"
        assert loaded.provider_metadata == {"test": True}
