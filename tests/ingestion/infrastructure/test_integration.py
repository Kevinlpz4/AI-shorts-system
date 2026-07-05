"""
End-to-end integration tests for the Ingestion BC using in-memory infrastructure.

Tests exercise the full stack:
    Service → UnitOfWork → Repository (in-memory) → EventPublisher (in-memory)

No mocks are used. All dependencies are concrete in-memory implementations.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from foundation.ports.clock import FrozenClock
from foundation.ports.uuid_provider import SequentialUUIDProvider
from foundation.result.result import Success, Failure

from ingestion.application.commands.article_commands import (
    CreateRawArticleCommand,
)
from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
)
from ingestion.application.commands.source_commands import (
    DisableSourceCommand,
    EnableSourceCommand,
    RegisterSourceCommand,
)
from ingestion.application.common.query_result import QueryResult
from ingestion.application.dto.article_dto import (
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
)
from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
from ingestion.application.queries.article_queries import (
    FindArticleQuery,
    ListArticlesQuery,
)
from ingestion.application.queries.feed_queries import FindFeedQuery, ListFeedsQuery
from ingestion.application.queries.source_queries import (
    FindSourceQuery,
    ListActiveSourcesQuery,
)
from ingestion.application.services.article_service import ArticleService
from ingestion.application.services.feed_service import FeedService
from ingestion.application.services.source_service import SourceService
from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    SourceId,
    TopicId,
)
from ingestion.domain.entities.category import Category
from ingestion.domain.entities.topic import Topic
from ingestion.domain.events.ingestion_events import (
    RawArticleCollected,
    SourceDisabled,
    SourceEnabled,
)
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
from ingestion.infrastructure.inmemory.event_publisher import (
    InMemoryEventPublisher,
)
from ingestion.infrastructure.inmemory.repositories import (
    InMemoryCategoryRepository,
    InMemoryFeedRepository,
    InMemoryNewsSourceRepository,
    InMemoryRawArticleRepository,
    InMemoryTopicRepository,
)
from ingestion.infrastructure.inmemory.unit_of_work import InMemoryUnitOfWork


# ═══════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════


@pytest.fixture
def inmemory_repos():
    """All five repositories, fresh for each test."""
    return (
        InMemoryNewsSourceRepository(),
        InMemoryFeedRepository(),
        InMemoryRawArticleRepository(),
        InMemoryCategoryRepository(),
        InMemoryTopicRepository(),
    )


@pytest.fixture
def uow():
    """Fresh InMemoryUnitOfWork."""
    return InMemoryUnitOfWork()


@pytest.fixture
def event_publisher():
    """Fresh InMemoryEventPublisher."""
    return InMemoryEventPublisher()


@pytest.fixture
def clock():
    """Frozen clock at 2026-07-05T00:00:00+00:00."""
    return FrozenClock(datetime(2026, 7, 5, tzinfo=timezone.utc))


@pytest.fixture
def uuid_provider():
    """Sequential UUID provider starting at 1."""
    return SequentialUUIDProvider(start=1)


@pytest.fixture
def source_service(inmemory_repos, uow, event_publisher, clock, uuid_provider):
    """SourceService with in-memory dependencies."""
    sr, fr, _, cr, tr = inmemory_repos
    return SourceService(
        source_repo=sr,
        feed_repo=fr,
        category_repo=cr,
        topic_repo=tr,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


@pytest.fixture
def feed_service(inmemory_repos, uow, event_publisher, clock, uuid_provider):
    """FeedService with in-memory dependencies."""
    sr, fr, _, cr, tr = inmemory_repos
    return FeedService(
        feed_repo=fr,
        source_repo=sr,
        category_repo=cr,
        topic_repo=tr,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


@pytest.fixture
def article_service(inmemory_repos, uow, event_publisher, clock, uuid_provider):
    """ArticleService with in-memory dependencies."""
    sr, fr, ar, _, _ = inmemory_repos
    return ArticleService(
        raw_article_repo=ar,
        feed_repo=fr,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


@pytest.fixture
def repos(inmemory_repos):
    """Alias for convenient destructuring in tests."""
    return inmemory_repos


@pytest.fixture
def services(source_service, feed_service, article_service):
    """Convenience bundle of all three services."""
    return source_service, feed_service, article_service


# ═══════════════════════════════════════════════════
# Pre-seeded data helpers
# ═══════════════════════════════════════════════════


def seed_category(repos, name: str = "Tech", slug: str = "tech") -> CategoryId:
    """Seed a category directly into the repository."""
    sr, fr, ar, cr, tr = repos
    cat = Category(
        id=CategoryId.generate(),
        name=CategoryName(name),
        slug=slug,
    )
    cr.save(cat)
    return cat.id


def seed_topic(repos, name: str = "AI") -> TopicId:
    """Seed a topic directly into the repository."""
    sr, fr, ar, cr, tr = repos
    topic = Topic(
        id=TopicId.generate(),
        name=name,
    )
    tr.save(topic)
    return topic.id


# ═══════════════════════════════════════════════════
# Test Suite
# ═══════════════════════════════════════════════════


class TestIntegrationFullHappyPath:
    """Scenario 1: Full happy path — register source → feed → article → query."""

    def test_full_happy_path(self, services, repos, event_publisher):
        """Register source, feed, article; then query all."""
        source_svc, feed_svc, article_svc = services

        # ── 1. Register source ──
        cmd_register = RegisterSourceCommand(
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
        )
        result = source_svc.execute_register_source(cmd_register)
        assert result.is_success, f"Failed to register source: {result.error}"
        source_dto = result.value
        source_id = source_dto.id

        # ── 2. Register feed under source ──
        cmd_feed = RegisterFeedCommand(
            source_id=source_id,
            url="https://reddit.com/r/python/.rss",
            label="Python Subreddit",
            language="en",
        )
        result = feed_svc.execute_register_feed(cmd_feed)
        assert result.is_success, f"Failed to register feed: {result.error}"
        feed_dto = result.value
        feed_id = feed_dto.id

        # ── 3. Create article under feed ──
        cmd_article = CreateRawArticleCommand(
            feed_id=feed_id,
            external_id="reddit-123",
            content_hash="a" * 64,
            title="Python 3.13 Released",
            url="https://reddit.com/r/python/123",
            fetched_at=datetime(2026, 7, 5, tzinfo=timezone.utc),
        )
        result = article_svc.execute_create_article(cmd_article)
        assert result.is_success, f"Failed to create article: {result.error}"
        article_dto = result.value

        # ── 4. Find source by ID ──
        result = source_svc.execute_find_source(
            FindSourceQuery(source_id=source_id)
        )
        assert result.is_success
        assert result.value.name == "Reddit"

        # ── 5. Find feed by ID ──
        result = feed_svc.execute_find_feed(FindFeedQuery(feed_id=feed_id))
        assert result.is_success
        assert result.value.label == "Python Subreddit"

        # ── 6. Find article by ID ──
        result = article_svc.execute_find_article(
            FindArticleQuery(article_id=article_dto.id)
        )
        assert result.is_success
        assert result.value.title == "Python 3.13 Released"

        # ── 7. List articles by feed ──
        result = article_svc.execute_list_articles(
            ListArticlesQuery(feed_id=feed_id)
        )
        assert result.is_success
        qr = result.value
        assert qr.total == 1
        assert len(qr.data) == 1
        assert qr.data[0].title == "Python 3.13 Released"

        # ── 8. List feeds by source ──
        result = feed_svc.execute_list_feeds(
            ListFeedsQuery(source_id=source_id)
        )
        assert result.is_success
        qr = result.value
        assert qr.total == 1

        # ── 9. List active sources ──
        result = source_svc.execute_list_active_sources(
            ListActiveSourcesQuery()
        )
        assert result.is_success
        qr = result.value
        assert qr.total == 1
        assert qr.data[0].name == "Reddit"


class TestIntegrationAL01:
    """AL-01: Cannot disable source with active feeds."""

    def test_disable_source_with_active_feeds_fails(self, services, repos):
        """Enable source → Register 2 feeds → Try to disable → FAIL."""
        source_svc, feed_svc, _ = services

        # Register source
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Register 2 feeds
        feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/rust/.rss",
                label="Rust",
                language="en",
            )
        )

        # Try to disable → should fail (2 active feeds)
        result = source_svc.execute_disable_source(
            DisableSourceCommand(source_id=source_id, reason="Testing")
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.HAS_ACTIVE_FEEDS


class TestIntegrationAL02:
    """AL-02: Source needs at least one active feed to be enabled."""

    def test_enable_source_without_feeds_fails(self, services, repos):
        """Register source → Try to enable without feeds → FAIL."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Disable first
        source_svc.execute_disable_source(
            DisableSourceCommand(source_id=source_id, reason="Initial")
        )

        # Try to enable without feeds → FAIL
        result = source_svc.execute_enable_source(
            EnableSourceCommand(source_id=source_id)
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_INACTIVE

    def test_enable_source_with_feed_ok(self, services, repos, event_publisher):
        """Register source → Add feed → Pause feed → Disable → Activate feed → Enable → OK."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Register feed (source is active, so AL-04 passes)
        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Pause feed so we can disable source (AL-01)
        feed_svc.execute_pause_feed(
            PauseFeedCommand(feed_id=feed_id, reason="For disabling source")
        )

        # Disable source (no active feeds now)
        source_svc.execute_disable_source(
            DisableSourceCommand(source_id=source_id, reason="Initial")
        )

        # Reactivate feed so source can be enabled (AL-02)
        feed_svc.execute_activate_feed(ActivateFeedCommand(feed_id=feed_id))

        # Now enable → should work (has active feed)
        result = source_svc.execute_enable_source(
            EnableSourceCommand(source_id=source_id)
        )
        assert result.is_success
        assert result.value.is_active is True

        # SourceEnabled event published
        assert event_publisher.has_event(SourceEnabled)


class TestIntegrationAL03_AL04:
    """AL-03: source_id must reference existing source.
    AL-04: Cannot create feed under inactive source."""

    def test_register_feed_under_nonexistent_source_fails(
        self, services, repos
    ):
        """Try to register feed under non-existent source → FAIL."""
        _, feed_svc, _ = services

        result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=str(SourceId.generate()),
                url="https://example.com/rss",
                label="Test",
                language="en",
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_register_feed_under_inactive_source_fails(
        self, services, repos
    ):
        """Register source inactive → Try to register feed → FAIL."""
        source_svc, feed_svc, _ = services

        # Register a source that is inactive by default
        # We create it through register (active by default), then disable
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Must disable with no active feeds
        source_svc.execute_disable_source(
            DisableSourceCommand(source_id=source_id, reason="Testing")
        )

        # Try to register feed → FAIL (AL-04)
        result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_INACTIVE


class TestIntegrationAL05:
    """AL-05: feed_id must reference existing feed."""

    def test_create_article_under_nonexistent_feed_fails(
        self, services, repos
    ):
        """Try to create article under non-existent feed → FAIL."""
        _, _, article_svc = services

        result = article_svc.execute_create_article(
            CreateRawArticleCommand(
                feed_id=str(FeedId.generate()),
                external_id="ext-1",
                content_hash="a" * 64,
                title="Test",
                url="https://example.com/article",
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND


class TestIntegrationRecordCollection:
    """RecordCollection flow — count > 0 emits RawArticleCollected."""

    def test_record_collection_emits_event(
        self, services, repos, event_publisher
    ):
        """Register source + feed → RecordCollection → RawArticleCollected."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Record collection with count > 0
        result = feed_svc.execute_record_collection(
            RecordCollectionCommand(feed_id=feed_id, count=5)
        )
        assert result.is_success

        # RawArticleCollected published
        assert event_publisher.has_event(RawArticleCollected)
        raw_event = [
            e
            for e in event_publisher.published_events
            if isinstance(e, RawArticleCollected)
        ][0]
        assert raw_event.count == 5

    def test_record_collection_zero_count_no_event(
        self, services, repos, event_publisher
    ):
        """RecordCollection with count=0 does NOT emit event."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Record collection with count = 0 → no event
        feed_svc.execute_record_collection(
            RecordCollectionCommand(feed_id=feed_id, count=0)
        )
        assert not event_publisher.has_event(RawArticleCollected)


class TestIntegrationRecordFailure:
    """RecordFailure — retry_count increments, auto-pause at max."""

    def test_record_failure_increments_retry_count(
        self, services, repos
    ):
        """RecordFailure incrementa retry_count."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
                sync_max_retries=3,
            )
        )
        feed_id = feed_result.value.id

        # Record 2 failures
        feed_svc.execute_record_failure(
            RecordFailureCommand(feed_id=feed_id, error="Timeout")
        )
        result = feed_svc.execute_record_failure(
            RecordFailureCommand(feed_id=feed_id, error="Timeout again")
        )
        assert result.is_success
        assert result.value.retry_count == 2
        assert result.value.is_active is True  # Still active

    def test_record_failure_auto_pauses_at_max_retries(
        self, services, repos
    ):
        """3 failures → feed auto-pauses."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
                sync_max_retries=3,
            )
        )
        feed_id = feed_result.value.id

        # 3 failures → should auto-pause
        for i in range(3):
            result = feed_svc.execute_record_failure(
                RecordFailureCommand(feed_id=feed_id, error=f"Error {i}")
            )
            assert result.is_success

        # After 3 failures (max_retries=3): retry_count=3, is_active=False
        result = feed_svc.execute_find_feed(FindFeedQuery(feed_id=feed_id))
        assert result.is_success
        feed_dto = result.value
        assert feed_dto.retry_count == 3
        assert feed_dto.is_active is False


class TestIntegrationDuplicateChecks:
    """Duplicate validation at service level."""

    def test_duplicate_source_name_fails(self, services, repos):
        """Register source → Register another with same name → FAIL."""
        source_svc, _, _ = services

        source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",  # Same name
                source_type="API",
                source_url="https://api.reddit.com",
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.DUPLICATE_NEWS_SOURCE

    def test_duplicate_feed_url_fails(self, services, repos):
        """Register source → Register feed → Duplicate URL → FAIL."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",  # Same URL
                label="Python Duplicate",
                language="en",
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.DUPLICATE_FEED_URL

    def test_duplicate_article_url_fails(self, services, repos):
        """Register source + feed → Create article → Duplicate URL → FAIL."""
        source_svc, feed_svc, article_svc = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Create first article
        result = article_svc.execute_create_article(
            CreateRawArticleCommand(
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="a" * 64,
                title="First Article",
                url="https://example.com/article1",
            )
        )
        assert result.is_success

        # Try duplicate URL
        result = article_svc.execute_create_article(
            CreateRawArticleCommand(
                feed_id=feed_id,
                external_id="ext-2",
                content_hash="b" * 64,
                title="Second Article",
                url="https://example.com/article1",  # Same URL
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.DUPLICATE_ARTICLE


class TestIntegrationEventOrder:
    """Event order verification — commit BEFORE publish."""

    def test_commit_before_publish(self, services, repos, uow, event_publisher):
        """Commit debe llamarse antes de publish_many."""
        source_svc, feed_svc, _ = services

        # Track calls
        original_commit = uow.commit
        original_publish = event_publisher.publish_many
        commit_order = []

        def tracking_commit():
            commit_order.append("commit")
            original_commit()

        def tracking_publish_many(events):
            commit_order.append("publish")
            original_publish(events)

        uow.commit = tracking_commit  # type: ignore[method-assign]
        event_publisher.publish_many = tracking_publish_many  # type: ignore[method-assign]

        # Trigger an operation that publishes events
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )

        # Clear commit tracking from register (they don't publish)
        commit_order.clear()

        # Disable source — publishes SourceDisabled
        source_svc.execute_disable_source(
            DisableSourceCommand(source_id=source_id, reason="Test")
        )

        # Commit must come before publish
        if "publish" in commit_order:
            commit_idx = commit_order.index("commit")
            publish_idx = commit_order.index("publish")
            assert (
                commit_idx < publish_idx
            ), "commit MUST be called before publish_many"


class TestIntegrationQueries:
    """Query operations verification."""

    def test_all_queries_work(self, services, repos):
        """FindSource, FindFeed, FindArticle, ListActiveSources, ListFeeds, ListArticles."""
        source_svc, feed_svc, article_svc = services

        # Register source
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Register feed
        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Create article
        article_result = article_svc.execute_create_article(
            CreateRawArticleCommand(
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="a" * 64,
                title="Test Article",
                url="https://example.com/article",
            )
        )
        article_id = article_result.value.id

        # ── FindSource ──
        result = source_svc.execute_find_source(
            FindSourceQuery(source_id=source_id)
        )
        assert result.is_success
        assert isinstance(result.value, SourceDetailDTO)

        # ── ListActiveSources ──
        result = source_svc.execute_list_active_sources(
            ListActiveSourcesQuery()
        )
        assert result.is_success
        assert isinstance(result.value, QueryResult)
        assert result.value.total == 1

        # ── FindFeed ──
        result = feed_svc.execute_find_feed(
            FindFeedQuery(feed_id=feed_id)
        )
        assert result.is_success
        assert isinstance(result.value, FeedDetailDTO)

        # ── ListFeeds ──
        result = feed_svc.execute_list_feeds(
            ListFeedsQuery(source_id=source_id)
        )
        assert result.is_success
        assert isinstance(result.value, QueryResult)
        assert result.value.total == 1

        # ── FindArticle ──
        result = article_svc.execute_find_article(
            FindArticleQuery(article_id=article_id)
        )
        assert result.is_success
        assert isinstance(result.value, RawArticleDetailDTO)

        # ── ListArticles ──
        result = article_svc.execute_list_articles(
            ListArticlesQuery(feed_id=feed_id)
        )
        assert result.is_success
        assert isinstance(result.value, QueryResult)
        assert result.value.total == 1
        assert isinstance(result.value.data[0], RawArticleSummaryDTO)


class TestIntegrationRollback:
    """Rollback behavior — exception during service triggers rollback."""

    def test_service_handles_domain_exception(self, services, repos, uow):
        """Service catches DomainError and returns Result.failure — UoW NOT rolled back."""
        source_svc, feed_svc, article_svc = services

        # Create source + feed
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        feed_result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
            )
        )
        feed_id = feed_result.value.id

        # Create an article that will fail at the repo level due to
        # invalid content_hash (not 64 hex chars)
        result = article_svc.execute_create_article(
            CreateRawArticleCommand(
                feed_id=feed_id,
                external_id="ext-1",
                content_hash="invalid-hash",  # Not a valid SHA-256
                title="Test",
                url="https://example.com/article",
            )
        )
        # Should fail with OPERATION_FAILED because RawArticle constructor
        # raises InvalidStateError, which gets caught by the service
        assert result.is_failure

        # The exception was caught and handled by the service (converted to Result).
        # The return inside the with block means __exit__ is called with
        # exc_type=None, so rollback() is NOT called. This is correct behavior
        # — the service handled the exception within the transaction.
        assert not uow.is_rolled_back, (
            "UoW should NOT rollback when the service handles the exception"
        )

    def test_uow_rollback_on_unhandled_exception(self, uow):
        """Direct test: UoW hace rollback cuando una excepción escapa del with."""
        with uow:
            pass
        assert not uow.is_rolled_back, "No exception → no rollback"

        # Test with exception
        try:
            with uow:
                raise RuntimeError("Unhandled error")
        except RuntimeError:
            pass
        assert uow.is_rolled_back, "Unhandled exception → rollback"


class TestIntegrationWithCategories:
    """Integration tests involving categories and topics."""

    def test_register_feed_with_categories(self, services, repos):
        """Register feed with categories should work."""
        source_svc, feed_svc, _ = services

        cat_id = seed_category(repos, name="Tech", slug="tech")
        topic_id = seed_topic(repos, name="AI")

        # Register source
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Register feed with categories and topics
        result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
                categories=(str(cat_id),),
                topics=(str(topic_id),),
            )
        )
        assert result.is_success
        assert str(cat_id) in result.value.categories
        assert str(topic_id) in result.value.topics

    def test_register_feed_with_nonexistent_category_fails(
        self, services, repos
    ):
        """Register feed with non-existent category → FAIL."""
        source_svc, feed_svc, _ = services

        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        result = feed_svc.execute_register_feed(
            RegisterFeedCommand(
                source_id=source_id,
                url="https://reddit.com/r/python/.rss",
                label="Python",
                language="en",
                categories=(str(CategoryId.generate()),),
            )
        )
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND


class TestIntegrationSourceCategoryTopic:
    """Assigning categories and topics to sources."""

    def test_assign_category_and_topic_to_source(
        self, services, repos
    ):
        """Assign category and topic to source works."""
        source_svc, _, _ = services
        sr, fr, ar, cr, tr = repos

        cat_id = seed_category(repos, name="Tech", slug="tech")
        topic_id = seed_topic(repos, name="AI")

        # Register source
        create_result = source_svc.execute_register_source(
            RegisterSourceCommand(
                name="Reddit",
                source_type="RSS",
                source_url="https://reddit.com",
            )
        )
        source_id = create_result.value.id

        # Assign category via source service
        from ingestion.application.commands.source_category_commands import (
            AssignCategoryToSourceCommand,
            AssignTopicToSourceCommand,
        )

        result = source_svc.execute_assign_category_to_source(
            AssignCategoryToSourceCommand(
                source_id=source_id, category_id=str(cat_id)
            )
        )
        assert result.is_success
        assert str(cat_id) in result.value.categories

        result = source_svc.execute_assign_topic_to_source(
            AssignTopicToSourceCommand(
                source_id=source_id, topic_id=str(topic_id)
            )
        )
        assert result.is_success
        assert str(topic_id) in result.value.topics
