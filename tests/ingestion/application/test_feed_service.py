"""Tests for FeedService — 15 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result, Success

from ingestion.application.commands.feed_category_commands import (
    AssignCategoryToFeedCommand,
    AssignTopicToFeedCommand,
)
from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
    UpdateFeedCommand,
)
from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.application.mappers.feed_mapper import FeedMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.feed_queries import FindFeedQuery, ListFeedsQuery
from ingestion.application.services.feed_service import FeedService
from ingestion.application.common.query_result import QueryResult
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import CategoryId, FeedId, SourceId, TopicId
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.events.ingestion_events import RawArticleCollected
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


# ── Mocks ──


class MockNewsSourceRepository:
    """Mock de NewsSourceRepository para tests."""

    def __init__(self) -> None:
        self._sources: dict[str, NewsSource] = {}

    def save(self, source: NewsSource) -> None:
        self._sources[str(source.id)] = source

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        key = str(id)
        if key in self._sources:
            return Result.success(self._sources[key])
        return Result.failure(
            Error(
                code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                message=f"Source '{id}' not found",
            )
        )

    def exists_by_name(self, name: str) -> bool:
        return False

    def find_all(self) -> list[NewsSource]:
        return list(self._sources.values())

    def find_active(self) -> list[NewsSource]:
        return [s for s in self._sources.values() if s.is_active]


class MockFeedRepository:
    """Mock de FeedRepository para tests."""

    def __init__(self) -> None:
        self._feeds: dict[str, Feed] = {}
        self._source_urls: set[tuple[str, str]] = set()

    def save(self, feed: Feed) -> None:
        self._feeds[str(feed.id)] = feed
        # Track URL uniqueness per source
        self._source_urls.add((str(feed.source_id), feed.url.value))

    def find_by_id(self, id: FeedId) -> Result[Feed]:
        key = str(id)
        if key in self._feeds:
            return Result.success(self._feeds[key])
        return Result.failure(
            Error(
                code=IngestionErrorCode.FEED_NOT_FOUND,
                message=f"Feed '{id}' not found",
            )
        )

    def find_by_source(self, source_id: SourceId) -> list[Feed]:
        sid = str(source_id)
        return [f for f in self._feeds.values() if str(f.source_id) == sid]

    def find_active_by_source(self, source_id: SourceId) -> list[Feed]:
        sid = str(source_id)
        return [f for f in self._feeds.values() if str(f.source_id) == sid and f.is_active]

    def exists_by_source_and_url(self, source_id: SourceId, url: ArticleUrl) -> bool:
        return (str(source_id), url.value) in self._source_urls

    def count_active_by_source(self, source_id: SourceId) -> int:
        return len(self.find_active_by_source(source_id))


class MockCategoryRepository:
    """Mock de CategoryRepository para tests."""

    def __init__(self) -> None:
        self._categories: set[str] = set()

    def find_by_id(self, id: CategoryId) -> Result[object]:
        if str(id) in self._categories:
            return Result.success(object())
        return Result.failure(
            Error(
                code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                message=f"Category '{id}' not found",
            )
        )

    def save(self, category: object) -> None:
        pass


class MockTopicRepository:
    """Mock de TopicRepository para tests."""

    def __init__(self) -> None:
        self._topics: set[str] = set()

    def find_by_id(self, id: TopicId) -> Result[object]:
        if str(id) in self._topics:
            return Result.success(object())
        return Result.failure(
            Error(
                code=IngestionErrorCode.TOPIC_NOT_FOUND,
                message=f"Topic '{id}' not found",
            )
        )

    def save(self, topic: object) -> None:
        pass


class MockUnitOfWork:
    """Mock de UnitOfWork para tests."""

    def __init__(self) -> None:
        self.commit_called = False
        self.rollback_called = False

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type is not None:
            self.rollback_called = True

    def commit(self) -> None:
        self.commit_called = True

    def rollback(self) -> None:
        self.rollback_called = True


class MockEventPublisher:
    """Mock de EventPublisher para tests."""

    def __init__(self) -> None:
        self.published: list = []

    def publish(self, event: object) -> None:
        self.published.append(event)

    def publish_many(self, events: list) -> None:
        self.published.extend(events)


class MockClock:
    """Mock de ClockPort para tests."""

    def now(self) -> datetime:
        return datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)


class MockUUIDProvider:
    """Mock de UUIDProvider para tests."""

    def __init__(self) -> None:
        self._counter = 1

    def new(self) -> UUID:
        result = UUID(int=self._counter)
        self._counter += 1
        return result


# ── Helpers ──


def make_source(
    name: str = "TestSource",
    is_active: bool = True,
) -> NewsSource:
    """Crea un NewsSource para tests."""
    return NewsSource(
        id=SourceId.generate(),
        name=name,
        source_type=SourceType.RSS,
        source_url=SourceUrl("https://example.com"),
        is_active=is_active,
    )


def make_feed(
    source_id: SourceId | None = None,
    url: str = "https://example.com/feed.xml",
    is_active: bool = True,
    retry_count: int = 0,
    sync_policy: SyncPolicy | None = None,
) -> Feed:
    """Crea un Feed para tests."""
    return Feed(
        id=FeedId.generate(),
        source_id=source_id or SourceId.generate(),
        url=ArticleUrl(url),
        label=ArticleTitle("Test Feed"),
        language=Language("en"),
        is_active=is_active,
        sync_policy=sync_policy or SyncPolicy(mode=SyncMode.PULL, interval_minutes=30),
        retry_count=retry_count,
    )


# ── Tests ──


class TestFeedService:
    """Suite de tests para FeedService."""

    def _make_service(self) -> tuple[FeedService, MockFeedRepository, MockNewsSourceRepository, MockCategoryRepository, MockTopicRepository, MockUnitOfWork, MockEventPublisher]:
        """Crea service con mocks fresh."""
        feed_repo = MockFeedRepository()
        source_repo = MockNewsSourceRepository()
        cat_repo = MockCategoryRepository()
        topic_repo = MockTopicRepository()
        uow = MockUnitOfWork()
        publisher = MockEventPublisher()
        clock = MockClock()
        uuid_provider = MockUUIDProvider()

        service = FeedService(
            feed_repo=feed_repo,
            source_repo=source_repo,
            category_repo=cat_repo,
            topic_repo=topic_repo,
            uow=uow,
            event_publisher=publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service, feed_repo, source_repo, cat_repo, topic_repo, uow, publisher

    # ── execute_register_feed ──

    def test_register_feed_happy_path(self) -> None:
        """register_feed debe crear un feed bajo un source activo."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source(is_active=True)
        source_repo.save(source)

        cmd = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Test Feed",
            language="en",
            sync_mode="PULL",
            sync_interval_minutes=30,
        )
        result = service.execute_register_feed(cmd)
        assert result.is_success
        dto = result.value
        assert isinstance(dto, FeedDetailDTO)
        assert dto.label == "Test Feed"
        assert dto.is_active is True
        assert dto.language == "en"
        assert dto.sync_mode == "PULL"

    def test_register_feed_source_not_found(self) -> None:
        """register_feed debe fallar si source no existe (AL-03)."""
        service, *_ = self._make_service()

        cmd = RegisterFeedCommand(
            source_id="00000000-0000-0000-0000-000000000999",
            url="https://example.com/feed.xml",
            label="Test",
            language="en",
        )
        result = service.execute_register_feed(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_NOT_FOUND

    def test_register_feed_source_inactive(self) -> None:
        """register_feed debe fallar si source está inactivo (AL-04)."""
        service, _, source_repo, *_ = self._make_service()

        source = make_source(is_active=False)
        source_repo.save(source)

        cmd = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Test",
            language="en",
        )
        result = service.execute_register_feed(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_INACTIVE

    def test_register_feed_duplicate_url(self) -> None:
        """register_feed debe fallar si la URL ya existe en el source."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source(is_active=True)
        source_repo.save(source)

        # Crear primer feed
        cmd1 = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Feed 1",
            language="en",
        )
        result1 = service.execute_register_feed(cmd1)
        assert result1.is_success

        # Intentar crear otro con la misma URL
        cmd2 = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Feed 2",
            language="en",
        )
        result2 = service.execute_register_feed(cmd2)
        assert result2.is_failure
        assert result2.error.code == IngestionErrorCode.DUPLICATE_FEED_URL

    def test_register_feed_with_categories_and_topics(self) -> None:
        """register_feed debe crear feed con categorías y topics."""
        service, feed_repo, source_repo, cat_repo, topic_repo, *_ = self._make_service()

        source = make_source(is_active=True)
        source_repo.save(source)

        cat_id = str(CategoryId.generate())
        topic_id = str(TopicId.generate())
        cat_repo._categories.add(cat_id)
        topic_repo._topics.add(topic_id)

        cmd = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Test Feed",
            language="en",
            categories=(cat_id,),
            topics=(topic_id,),
        )
        result = service.execute_register_feed(cmd)
        assert result.is_success
        assert cat_id in result.value.categories
        assert topic_id in result.value.topics

    # ── execute_update_feed ──

    def test_update_feed_happy_path(self) -> None:
        """update_feed debe actualizar campos provistos."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id)
        feed_repo.save(feed)

        cmd = UpdateFeedCommand(
            feed_id=str(feed.id),
            label="Updated Label",
            url="https://example.com/new-feed.xml",
        )
        result = service.execute_update_feed(cmd)
        assert result.is_success
        assert result.value.label == "Updated Label"
        assert result.value.url == "https://example.com/new-feed.xml"

    # ── execute_pause_feed ──

    def test_pause_feed(self) -> None:
        """pause_feed debe marcar el feed como inactivo."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id, is_active=True)
        feed_repo.save(feed)

        cmd = PauseFeedCommand(feed_id=str(feed.id), reason="Testing pause")
        result = service.execute_pause_feed(cmd)
        assert result.is_success
        assert result.value.is_active is False

    # ── execute_activate_feed ──

    def test_activate_feed(self) -> None:
        """activate_feed debe marcar el feed como activo y resetear retry_count."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id, is_active=False, retry_count=3)
        feed_repo.save(feed)

        cmd = ActivateFeedCommand(feed_id=str(feed.id))
        result = service.execute_activate_feed(cmd)
        assert result.is_success
        assert result.value.is_active is True
        assert result.value.retry_count == 0

    # ── execute_record_collection ──

    def test_record_collection_with_count_emits_event(self) -> None:
        """record_collection con count > 0 debe publicar RawArticleCollected."""
        service, feed_repo, source_repo, _, _, _, publisher = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id)
        feed_repo.save(feed)

        cmd = RecordCollectionCommand(feed_id=str(feed.id), count=5)
        result = service.execute_record_collection(cmd)
        assert result.is_success

        # Verificar que se publicó el evento
        assert len(publisher.published) == 1
        assert isinstance(publisher.published[0], RawArticleCollected)
        assert publisher.published[0].count == 5

        # Verificar que retry_count se reseteó
        assert result.value.retry_count == 0

    def test_record_collection_zero_count_no_event(self) -> None:
        """record_collection con count == 0 NO debe publicar eventos."""
        service, feed_repo, source_repo, _, _, _, publisher = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id, retry_count=2)
        feed_repo.save(feed)

        cmd = RecordCollectionCommand(feed_id=str(feed.id), count=0)
        result = service.execute_record_collection(cmd)
        assert result.is_success

        # No debe publicar eventos
        assert len(publisher.published) == 0

        # retry_count se resetea incluso con count=0
        assert result.value.retry_count == 0

    # ── execute_record_failure ──

    def test_record_failure_increments_retry_count(self) -> None:
        """record_failure debe incrementar retry_count."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id, retry_count=0)
        feed_repo.save(feed)

        cmd = RecordFailureCommand(feed_id=str(feed.id), error="Connection timeout")
        result = service.execute_record_failure(cmd)
        assert result.is_success
        assert result.value.retry_count == 1

    # ── execute_assign_category_to_feed ──

    def test_assign_category_to_feed_ok(self) -> None:
        """assign_category_to_feed debe asignar categoría existente."""
        service, feed_repo, source_repo, cat_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id)
        feed_repo.save(feed)

        cat_id = str(CategoryId.generate())
        cat_repo._categories.add(cat_id)

        cmd = AssignCategoryToFeedCommand(feed_id=str(feed.id), category_id=cat_id)
        result = service.execute_assign_category_to_feed(cmd)
        assert result.is_success
        assert cat_id in result.value.categories

    def test_assign_category_to_feed_not_found(self) -> None:
        """assign_category_to_feed debe fallar si categoría no existe."""
        service, *_ = self._make_service()
        cmd = AssignCategoryToFeedCommand(
            feed_id="00000000-0000-0000-0000-000000000001",
            category_id="00000000-0000-0000-0000-000000000099",
        )
        result = service.execute_assign_category_to_feed(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    # ── execute_assign_topic_to_feed ──

    def test_assign_topic_to_feed_ok(self) -> None:
        """assign_topic_to_feed debe asignar topic existente."""
        service, feed_repo, source_repo, _, topic_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id)
        feed_repo.save(feed)

        topic_id = str(TopicId.generate())
        topic_repo._topics.add(topic_id)

        cmd = AssignTopicToFeedCommand(feed_id=str(feed.id), topic_id=topic_id)
        result = service.execute_assign_topic_to_feed(cmd)
        assert result.is_success
        assert topic_id in result.value.topics

    def test_assign_topic_to_feed_not_found(self) -> None:
        """assign_topic_to_feed debe fallar si topic no existe."""
        service, *_ = self._make_service()
        cmd = AssignTopicToFeedCommand(
            feed_id="00000000-0000-0000-0000-000000000001",
            topic_id="00000000-0000-0000-0000-000000000099",
        )
        result = service.execute_assign_topic_to_feed(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    # ── Queries ──

    def test_find_feed_ok(self) -> None:
        """find_feed debe retornar feed por ID."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)
        feed = make_feed(source_id=source.id)
        feed_repo.save(feed)

        query = FindFeedQuery(feed_id=str(feed.id))
        result = service.execute_find_feed(query)
        assert result.is_success
        assert result.value.id == str(feed.id)

    def test_find_feed_not_found(self) -> None:
        """find_feed debe fallar si no existe."""
        service, *_ = self._make_service()

        query = FindFeedQuery(feed_id="00000000-0000-0000-0000-000000000999")
        result = service.execute_find_feed(query)
        assert result.is_failure
        # ErrorMapper.map_result_error mapea FEED_NOT_FOUND → RESOURCE_NOT_FOUND
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_list_feeds_ok(self) -> None:
        """list_feeds debe retornar feeds de un source."""
        service, feed_repo, source_repo, *_ = self._make_service()

        source = make_source()
        source_repo.save(source)

        feed1 = make_feed(source_id=source.id, url="https://example.com/feed1.xml")
        feed2 = make_feed(source_id=source.id, url="https://example.com/feed2.xml")
        feed_repo.save(feed1)
        feed_repo.save(feed2)

        query = ListFeedsQuery(source_id=str(source.id))
        result = service.execute_list_feeds(query)
        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 2
        assert len(qr.data) == 2

    def test_list_feeds_empty(self) -> None:
        """list_feeds debe retornar lista vacía si no hay feeds."""
        service, *_ = self._make_service()

        query = ListFeedsQuery(source_id="00000000-0000-0000-0000-000000000001")
        result = service.execute_list_feeds(query)
        assert result.is_success
        assert len(result.value.data) == 0
        assert result.value.total == 0

    # ── UoW commit verification ──

    def test_register_feed_calls_commit(self) -> None:
        """register_feed debe llamar a commit."""
        service, feed_repo, source_repo, _, _, uow, _ = self._make_service()

        source = make_source(is_active=True)
        source_repo.save(source)

        cmd = RegisterFeedCommand(
            source_id=str(source.id),
            url="https://example.com/feed.xml",
            label="Test",
            language="en",
        )
        result = service.execute_register_feed(cmd)
        assert result.is_success
        assert uow.commit_called is True
