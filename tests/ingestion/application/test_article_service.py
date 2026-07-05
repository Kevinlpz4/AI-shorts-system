"""Tests for ArticleService — 8 test cases covering all methods and AL-05."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result, Success

from ingestion.application.commands.article_commands import CreateRawArticleCommand
from ingestion.application.dto.article_dto import (
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
)
from ingestion.application.mappers.article_mapper import RawArticleMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.article_queries import (
    FindArticleQuery,
    ListArticlesQuery,
)
from ingestion.application.services.article_service import ArticleService
from ingestion.application.common.query_result import QueryResult
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import FeedId, RawArticleId
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


# ── Mocks ──


class MockFeedRepository:
    """Mock de FeedRepository para tests."""

    def __init__(self) -> None:
        self._feeds: dict[str, Feed] = {}

    def save(self, feed: Feed) -> None:
        self._feeds[str(feed.id)] = feed

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

    def find_by_source(self, source_id: object) -> list:
        return []

    def find_active_by_source(self, source_id: object) -> list:
        return []

    def exists_by_source_and_url(self, source_id: object, url: object) -> bool:
        return False

    def count_active_by_source(self, source_id: object) -> int:
        return 0


class MockRawArticleRepository:
    """Mock de RawArticleRepository para tests."""

    def __init__(self) -> None:
        self._articles: dict[str, RawArticle] = {}
        self._feed_urls: set[tuple[str, str]] = set()
        self._feed_hashes: set[tuple[str, str]] = set()

    def save(self, article: RawArticle) -> None:
        self._articles[str(article.id)] = article
        self._feed_urls.add((str(article.feed_id), article.url.value))
        self._feed_hashes.add((str(article.feed_id), article.content_hash))

    def save_batch(self, articles: list[RawArticle]) -> None:
        for a in articles:
            self.save(a)

    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]:
        key = str(id)
        if key in self._articles:
            return Result.success(self._articles[key])
        return Result.failure(
            Error(
                code=IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
                message=f"Article '{id}' not found",
            )
        )

    def find_by_feed(
        self, feed_id: FeedId, page: int = 1, size: int = 50
    ) -> list[RawArticle]:
        fid = str(feed_id)
        all_articles = [a for a in self._articles.values() if str(a.feed_id) == fid]
        start = (page - 1) * size
        end = start + size
        return all_articles[start:end]

    def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool:
        return (str(feed_id), url.value) in self._feed_urls

    def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool:
        return (str(feed_id), content_hash) in self._feed_hashes

    def count_by_feed(self, feed_id: FeedId) -> int:
        fid = str(feed_id)
        return sum(1 for a in self._articles.values() if str(a.feed_id) == fid)


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


def make_feed(feed_id: FeedId | None = None) -> Feed:
    """Crea un Feed básico para tests."""
    return Feed(
        id=feed_id or FeedId.generate(),
        source_id=FeedId.generate(),  # no necesitamos source real para article tests
        url=ArticleUrl("https://example.com/feed.xml"),
        label=ArticleTitle("Test Feed"),
        language=Language("en"),
        sync_policy=SyncPolicy(mode=SyncMode.PULL, interval_minutes=30),
    )


# ── Tests ──


class TestArticleService:
    """Suite de tests para ArticleService."""

    def _make_service(
        self,
    ) -> tuple[
        ArticleService,
        MockRawArticleRepository,
        MockFeedRepository,
        MockUnitOfWork,
        MockEventPublisher,
    ]:
        """Crea service con mocks fresh."""
        article_repo = MockRawArticleRepository()
        feed_repo = MockFeedRepository()
        uow = MockUnitOfWork()
        publisher = MockEventPublisher()
        clock = MockClock()
        uuid_provider = MockUUIDProvider()

        service = ArticleService(
            raw_article_repo=article_repo,
            feed_repo=feed_repo,
            uow=uow,
            event_publisher=publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service, article_repo, feed_repo, uow, publisher

    # ── execute_create_article ──

    def test_create_article_happy_path(self) -> None:
        """create_article debe crear un artículo y retornar RawArticleDetailDTO."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        cmd = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            title="Test Article",
            url="https://example.com/article-1",
            author="John Doe",
            language="en",
        )
        result = service.execute_create_article(cmd)
        assert result.is_success
        dto = result.value
        assert isinstance(dto, RawArticleDetailDTO)
        assert dto.title == "Test Article"
        assert dto.author == "John Doe"
        assert dto.external_id == "ext-001"
        assert dto.content_hash is not None
        assert dto.fetched_at is not None

    def test_create_article_feed_not_found(self) -> None:
        """create_article debe fallar si el feed no existe (AL-05)."""
        service, *_ = self._make_service()

        cmd = CreateRawArticleCommand(
            feed_id="00000000-0000-0000-0000-000000000999",
            external_id="ext-001",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            title="Test",
            url="https://example.com/article-1",
        )
        result = service.execute_create_article(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.FEED_NOT_FOUND

    def test_create_article_duplicate_url(self) -> None:
        """create_article debe fallar si la URL ya existe en el feed."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        # Crear primer artículo
        cmd1 = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            title="Article 1",
            url="https://example.com/article-1",
        )
        result1 = service.execute_create_article(cmd1)
        assert result1.is_success

        # Intentar crear otro con misma URL
        cmd2 = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-002",
            content_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            title="Article 2",
            url="https://example.com/article-1",  # misma URL
        )
        result2 = service.execute_create_article(cmd2)
        assert result2.is_failure
        assert result2.error.code == IngestionErrorCode.DUPLICATE_ARTICLE

    def test_create_article_duplicate_hash(self) -> None:
        """create_article debe fallar si el hash ya existe en el feed."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        content_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

        cmd1 = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash=content_hash,
            title="Article 1",
            url="https://example.com/article-1",
        )
        result1 = service.execute_create_article(cmd1)
        assert result1.is_success

        # Intentar crear otro con mismo hash
        cmd2 = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-002",
            content_hash=content_hash,  # mismo hash
            title="Article 2",
            url="https://example.com/article-2",
        )
        result2 = service.execute_create_article(cmd2)
        assert result2.is_failure
        assert result2.error.code == IngestionErrorCode.DUPLICATE_ARTICLE

    def test_create_article_uses_clock_when_no_fetched_at(self) -> None:
        """create_article debe usar clock.now() si fetched_at no se provee."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        cmd = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            title="Test",
            url="https://example.com/article-1",
            # fetched_at no se provee
        )
        result = service.execute_create_article(cmd)
        assert result.is_success
        # fetched_at debe ser el valor del clock mock
        assert result.value.fetched_at == datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)

    # ── Queries ──

    def test_find_article_ok(self) -> None:
        """find_article debe retornar artículo por ID."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        # Crear artículo primero
        create_cmd = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            title="Test Article",
            url="https://example.com/article-1",
        )
        create_result = service.execute_create_article(create_cmd)
        article_id = create_result.value.id

        query = FindArticleQuery(article_id=article_id)
        result = service.execute_find_article(query)
        assert result.is_success
        assert result.value.id == article_id
        assert result.value.title == "Test Article"

    def test_find_article_not_found(self) -> None:
        """find_article debe fallar si no existe."""
        service, *_ = self._make_service()

        query = FindArticleQuery(
            article_id="00000000-0000-0000-0000-000000000999"
        )
        result = service.execute_find_article(query)
        assert result.is_failure
        # ErrorMapper.map_result_error mapea RAW_ARTICLE_NOT_FOUND → RESOURCE_NOT_FOUND
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_list_articles_ok(self) -> None:
        """list_articles debe retornar artículos paginados."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        # Crear 3 artículos
        for i in range(3):
            service.execute_create_article(
                CreateRawArticleCommand(
                    feed_id=str(feed.id),
                    external_id=f"ext-{i:03d}",
                    content_hash=f"{i:064x}",
                    title=f"Article {i}",
                    url=f"https://example.com/article-{i}",
                )
            )

        query = ListArticlesQuery(feed_id=str(feed.id), page=1, size=10)
        result = service.execute_list_articles(query)
        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 3
        assert len(qr.data) == 3
        for dto in qr.data:
            assert isinstance(dto, RawArticleSummaryDTO)

    def test_list_articles_pagination(self) -> None:
        """list_articles debe paginar correctamente."""
        service, article_repo, feed_repo, *_ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        # Crear 5 artículos
        for i in range(5):
            service.execute_create_article(
                CreateRawArticleCommand(
                    feed_id=str(feed.id),
                    external_id=f"ext-{i:03d}",
                    content_hash=f"{i:064x}",
                    title=f"Article {i}",
                    url=f"https://example.com/article-{i}",
                )
            )

        # Página 1 con size=2
        query = ListArticlesQuery(feed_id=str(feed.id), page=1, size=2)
        result = service.execute_list_articles(query)
        assert result.is_success
        assert len(result.value.data) == 2
        assert result.value.total == 5
        assert result.value.page == 1
        assert result.value.size == 2

    # ── UoW commit verification ──

    def test_create_article_calls_commit(self) -> None:
        """create_article debe llamar a commit."""
        service, article_repo, feed_repo, uow, _ = self._make_service()

        feed = make_feed()
        feed_repo.save(feed)

        cmd = CreateRawArticleCommand(
            feed_id=str(feed.id),
            external_id="ext-001",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            title="Test",
            url="https://example.com/article-1",
        )
        result = service.execute_create_article(cmd)
        assert result.is_success
        assert uow.commit_called is True
