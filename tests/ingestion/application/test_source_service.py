"""Tests for SourceService — 11 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result, Success

from ingestion.application.commands.source_category_commands import (
    AssignCategoryToSourceCommand,
    AssignTopicToSourceCommand,
)
from ingestion.application.commands.source_commands import (
    DisableSourceCommand,
    EnableSourceCommand,
    RegisterSourceCommand,
    UpdateSourceCommand,
)
from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
from ingestion.application.mappers.source_mapper import SourceMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.source_queries import (
    FindSourceQuery,
    ListActiveSourcesQuery,
)
from ingestion.application.services.source_service import SourceService
from ingestion.application.common.query_result import QueryResult
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.domain.entities.ids import CategoryId, SourceId, TopicId
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.events.ingestion_events import SourceDisabled, SourceEnabled
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl


# ── Mocks ──


class MockNewsSourceRepository:
    """Mock de NewsSourceRepository para tests."""

    def __init__(self) -> None:
        self._sources: dict[str, NewsSource] = {}
        self._names: set[str] = set()

    def save(self, source: NewsSource) -> None:
        self._sources[str(source.id)] = source
        # Track names for exists_by_name
        # Clear all tracked names and re-index (simplifies updates)
        self._names = {s.name for s in self._sources.values()}

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
        return name in self._names

    def find_all(self) -> list[NewsSource]:
        return list(self._sources.values())

    def find_active(self) -> list[NewsSource]:
        return [s for s in self._sources.values() if s.is_active]


class MockFeedRepository:
    """Mock de FeedRepository para tests (solo métodos que SourceService usa)."""

    def __init__(self) -> None:
        self._active_counts: dict[str, int] = {}

    def count_active_by_source(self, source_id: SourceId) -> int:
        return self._active_counts.get(str(source_id), 0)

    def save(self, feed: object) -> None:
        pass

    def find_by_id(self, id: object) -> Result[object]:
        return Result.failure(Error(message="not implemented"))

    def find_by_source(self, source_id: object) -> list:
        return []

    def find_active_by_source(self, source_id: object) -> list:
        return []

    def exists_by_source_and_url(self, source_id: object, url: object) -> bool:
        return False


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
        self._entered = False

    def __enter__(self) -> UnitOfWork:
        self._entered = True
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
    source_type: SourceType = SourceType.RSS,
    source_url: str = "https://example.com",
    is_active: bool = True,
) -> NewsSource:
    """Crea un NewsSource para tests."""
    return NewsSource(
        id=SourceId.generate(),
        name=name,
        source_type=source_type,
        source_url=SourceUrl(source_url),
        is_active=is_active,
    )


# ── Fixtures ──


class TestSourceService:
    """Suite de tests para SourceService."""

    def _make_service(self) -> tuple[SourceService, MockNewsSourceRepository, MockFeedRepository, MockCategoryRepository, MockTopicRepository, MockUnitOfWork, MockEventPublisher]:
        """Crea service con mocks fresh."""
        source_repo = MockNewsSourceRepository()
        feed_repo = MockFeedRepository()
        cat_repo = MockCategoryRepository()
        topic_repo = MockTopicRepository()
        uow = MockUnitOfWork()
        publisher = MockEventPublisher()
        clock = MockClock()
        uuid_provider = MockUUIDProvider()

        service = SourceService(
            source_repo=source_repo,
            feed_repo=feed_repo,
            category_repo=cat_repo,
            topic_repo=topic_repo,
            uow=uow,
            event_publisher=publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service, source_repo, feed_repo, cat_repo, topic_repo, uow, publisher

    # ── execute_register_source ──

    def test_register_source_happy_path(self) -> None:
        """register_source debe crear un source y retornar SourceDetailDTO."""
        service, source_repo, *_ = self._make_service()

        cmd = RegisterSourceCommand(
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
        )
        result = service.execute_register_source(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, SourceDetailDTO)
        assert dto.name == "Reddit"
        assert dto.source_type == "RSS"
        assert dto.source_url == "https://reddit.com"
        assert dto.is_active is True

        # Verificar que se guardó en el repo
        assert len(source_repo._sources) == 1

    def test_register_source_duplicate_name(self) -> None:
        """register_source debe fallar si el nombre ya existe."""
        service, source_repo, *_ = self._make_service()

        # Crear un source primero
        cmd1 = RegisterSourceCommand(
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
        )
        result1 = service.execute_register_source(cmd1)
        assert result1.is_success

        # Intentar crear otro con el mismo nombre
        cmd2 = RegisterSourceCommand(
            name="Reddit",
            source_type="API",
            source_url="https://api.reddit.com",
        )
        result2 = service.execute_register_source(cmd2)
        assert result2.is_failure
        assert result2.error.code == IngestionErrorCode.DUPLICATE_NEWS_SOURCE

    # ── execute_update_source ──

    def test_update_source_happy_path(self) -> None:
        """update_source debe actualizar campos provistos."""
        service, source_repo, *_ = self._make_service()

        # Crear source primero
        create_cmd = RegisterSourceCommand(
            name="Reddit",
            source_type="RSS",
            source_url="https://old.reddit.com",
        )
        create_result = service.execute_register_source(create_cmd)
        assert create_result.is_success
        source_id = create_result.value.id

        # Actualizar
        update_cmd = UpdateSourceCommand(
            source_id=source_id,
            name="Reddit Updated",
            source_url="https://new.reddit.com",
        )
        result = service.execute_update_source(update_cmd)
        assert result.is_success
        dto = result.value
        assert dto.name == "Reddit Updated"
        assert dto.source_url == "https://new.reddit.com"
        assert dto.source_type == "RSS"  # No cambió

    def test_update_source_not_found(self) -> None:
        """update_source debe fallar si el source no existe."""
        service, *_ = self._make_service()

        cmd = UpdateSourceCommand(
            source_id="00000000-0000-0000-0000-000000000000",
            name="Nuevo",
        )
        result = service.execute_update_source(cmd)
        assert result.is_failure
        # ErrorMapper.map_result_error mapea NEWS_SOURCE_NOT_FOUND → RESOURCE_NOT_FOUND
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_update_source_duplicate_name(self) -> None:
        """update_source debe fallar si el nuevo nombre ya existe."""
        service, source_repo, *_ = self._make_service()

        # Crear dos sources
        service.execute_register_source(
            RegisterSourceCommand(name="Source1", source_type="RSS", source_url="https://a.com")
        )
        create2 = service.execute_register_source(
            RegisterSourceCommand(name="Source2", source_type="RSS", source_url="https://b.com")
        )
        source2_id = create2.value.id

        # Intentar cambiar Source2 a nombre de Source1
        cmd = UpdateSourceCommand(source_id=source2_id, name="Source1")
        result = service.execute_update_source(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.DUPLICATE_NEWS_SOURCE

    # ── execute_enable_source ──

    def test_enable_source_happy_path_emits_event(self) -> None:
        """enable_source debe habilitar y publicar SourceEnabled."""
        service, source_repo, feed_repo, _, _, _, publisher = self._make_service()

        # Crear source
        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id
        assert source_id is not None

        # Simular que tiene un feed activo (AL-02)
        feed_repo._active_counts[str(SourceId.from_string(source_id))] = 1

        # Deshabilitar primero
        source_repo._sources[source_id].is_active = False

        cmd = EnableSourceCommand(source_id=source_id)
        result = service.execute_enable_source(cmd)
        assert result.is_success
        assert result.value.is_active is True

        # Verificar que se publicó SourceEnabled
        assert len(publisher.published) == 1  # type: ignore[possibly-undefined]
        assert isinstance(publisher.published[0], SourceEnabled)  # type: ignore[possibly-undefined]

    def test_enable_source_no_active_feeds(self) -> None:
        """enable_source debe fallar si no hay feeds activos (AL-02)."""
        service, source_repo, feed_repo, *_ = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        # Sin feeds activos (count = 0 por defecto)
        source_repo._sources[source_id].is_active = False

        cmd = EnableSourceCommand(source_id=source_id)
        result = service.execute_enable_source(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.NEWS_SOURCE_INACTIVE

    # ── execute_disable_source ──

    def test_disable_source_happy_path_emits_event(self) -> None:
        """disable_source debe deshabilitar y publicar SourceDisabled."""
        service, source_repo, feed_repo, _, _, _, publisher = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        # Sin feeds activos (AL-01 pasa)
        cmd = DisableSourceCommand(source_id=source_id, reason="Testing")
        result = service.execute_disable_source(cmd)
        assert result.is_success
        assert result.value.is_active is False

        # Verificar que se publicó SourceDisabled
        assert len(publisher.published) == 1  # type: ignore[possibly-undefined]
        assert isinstance(publisher.published[0], SourceDisabled)  # type: ignore[possibly-undefined]

    def test_disable_source_with_active_feeds(self) -> None:
        """disable_source debe fallar si tiene feeds activos (AL-01)."""
        service, source_repo, feed_repo, *_ = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        # Simular que tiene un feed activo
        feed_repo._active_counts[str(SourceId.from_string(source_id))] = 2

        cmd = DisableSourceCommand(source_id=source_id, reason="Testing")
        result = service.execute_disable_source(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.HAS_ACTIVE_FEEDS

    # ── execute_assign_category_to_source ──

    def test_assign_category_to_source_ok(self) -> None:
        """assign_category_to_source debe asignar categoría existente."""
        service, source_repo, _, cat_repo, *_ = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        # Registrar categoría existente
        cat_id = str(CategoryId.generate())
        cat_repo._categories.add(cat_id)

        cmd = AssignCategoryToSourceCommand(source_id=source_id, category_id=cat_id)
        result = service.execute_assign_category_to_source(cmd)
        assert result.is_success
        assert cat_id in result.value.categories

    def test_assign_category_to_source_not_found(self) -> None:
        """assign_category_to_source debe fallar si categoría no existe."""
        service, *_ = self._make_service()

        cmd = AssignCategoryToSourceCommand(
            source_id="00000000-0000-0000-0000-000000000001",
            category_id="00000000-0000-0000-0000-000000000099",
        )
        result = service.execute_assign_category_to_source(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.CATEGORY_NOT_FOUND

    # ── execute_assign_topic_to_source ──

    def test_assign_topic_to_source_ok(self) -> None:
        """assign_topic_to_source debe asignar topic existente."""
        service, source_repo, _, _, topic_repo, *_ = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        # Registrar topic existente
        topic_id = str(TopicId.generate())
        topic_repo._topics.add(topic_id)

        cmd = AssignTopicToSourceCommand(source_id=source_id, topic_id=topic_id)
        result = service.execute_assign_topic_to_source(cmd)
        assert result.is_success
        assert topic_id in result.value.topics

    def test_assign_topic_to_source_not_found(self) -> None:
        """assign_topic_to_source debe fallar si topic no existe."""
        service, *_ = self._make_service()

        cmd = AssignTopicToSourceCommand(
            source_id="00000000-0000-0000-0000-000000000001",
            topic_id="00000000-0000-0000-0000-000000000099",
        )
        result = service.execute_assign_topic_to_source(cmd)
        assert result.is_failure
        assert result.error.code == IngestionErrorCode.TOPIC_NOT_FOUND

    # ── execute_find_source (query) ──

    def test_find_source_ok(self) -> None:
        """find_source debe retornar el source por ID."""
        service, *_ = self._make_service()

        create_result = service.execute_register_source(
            RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://test.com")
        )
        source_id = create_result.value.id

        query = FindSourceQuery(source_id=source_id)
        result = service.execute_find_source(query)
        assert result.is_success
        assert result.value.name == "Test"

    def test_find_source_not_found(self) -> None:
        """find_source debe fallar si no existe."""
        service, *_ = self._make_service()

        query = FindSourceQuery(source_id="00000000-0000-0000-0000-000000000999")
        result = service.execute_find_source(query)
        assert result.is_failure
        # ErrorMapper.map_result_error mapea NEWS_SOURCE_NOT_FOUND → RESOURCE_NOT_FOUND
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_list_active_sources (query) ──

    def test_list_active_sources_ok(self) -> None:
        """list_active_sources debe listar solo fuentes activas."""
        service, source_repo, *_ = self._make_service()

        # Crear una activa y una inactiva
        service.execute_register_source(
            RegisterSourceCommand(name="Active", source_type="RSS", source_url="https://a.com")
        )
        create2 = service.execute_register_source(
            RegisterSourceCommand(name="Inactive", source_type="RSS", source_url="https://b.com")
        )
        # Deshabilitar la segunda
        source_id2 = create2.value.id
        # Set inactive manually in repo
        source_repo._sources[source_id2].is_active = False

        query = ListActiveSourcesQuery()
        result = service.execute_list_active_sources(query)
        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 1
        assert len(qr.data) == 1
        assert qr.data[0].name == "Active"

    # ── UoW commit verification ──

    def test_register_source_calls_commit(self) -> None:
        """register_source debe llamar a commit."""
        service, source_repo, feed_repo, cat_repo, topic_repo, uow, publisher = self._make_service()

        cmd = RegisterSourceCommand(
            name="Test", source_type="RSS", source_url="https://test.com"
        )
        result = service.execute_register_source(cmd)
        assert result.is_success
        assert uow.commit_called is True
