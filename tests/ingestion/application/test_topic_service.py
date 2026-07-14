"""Tests for TopicService — CRUD, activation, queries for Topic."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result

from ingestion.application.commands.topic_commands import (
    ActivateTopicCommand,
    CreateTopicCommand,
    DeactivateTopicCommand,
    UpdateTopicCommand,
)
from ingestion.application.dto.topic_dto import TopicDetailDTO, TopicSummaryDTO
from ingestion.application.mappers.topic_mapper import TopicMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.topic_queries import (
    FindTopicQuery,
    ListTopicsQuery,
)
from ingestion.application.services.topic_service import TopicService
from ingestion.application.common.query_result import QueryResult
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.domain.entities.ids import TopicId
from ingestion.domain.entities.topic import Topic
from ingestion.domain.exceptions.errors import IngestionErrorCode


# ── Mocks ──


class MockTopicRepository:
    """Mock de TopicRepository para tests."""

    def __init__(self) -> None:
        self._topics: dict[str, Topic] = {}
        self._names: set[str] = set()

    def save(self, topic: Topic) -> None:
        self._topics[str(topic.id)] = topic
        self._names = {t.name for t in self._topics.values()}

    def find_by_id(self, id: TopicId) -> Result[Topic]:
        key = str(id)
        if key in self._topics:
            return Result.success(self._topics[key])
        return Result.failure(
            Error(
                code=IngestionErrorCode.TOPIC_NOT_FOUND,
                message=f"Topic '{id}' not found",
            )
        )

    def find_by_name(self, name: str) -> Result[Topic]:
        for t in self._topics.values():
            if t.name == name:
                return Result.success(t)
        return Result.failure(
            Error(
                code=IngestionErrorCode.TOPIC_NOT_FOUND,
                message=f"Topic with name '{name}' not found",
            )
        )

    def find_all(self) -> list[Topic]:
        return list(self._topics.values())

    def find_active(self) -> list[Topic]:
        return [t for t in self._topics.values() if t.is_active]

    def exists_by_name(self, name: str) -> bool:
        return name in self._names


class MockUnitOfWork:
    """Mock de UnitOfWork para tests."""

    def __init__(self) -> None:
        self.commit_called = False
        self.rollback_called = False
        self._entered = False

    def __enter__(self) -> UnitOfWork:
        self._entered = True
        return self

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
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


def _fixed_uuid_str(int_val: int) -> str:
    """Retorna un UUID string determinístico para tests."""
    return str(UUID(int=int_val))


# ── Tests ──


class TestTopicService:
    """Suite de tests para TopicService."""

    def _make_service(
        self,
    ) -> tuple[
        TopicService,
        MockTopicRepository,
        MockUnitOfWork,
        MockEventPublisher,
    ]:
        """Crea service con mocks fresh."""
        topic_repo = MockTopicRepository()
        uow = MockUnitOfWork()
        publisher = MockEventPublisher()
        clock = MockClock()
        uuid_provider = MockUUIDProvider()

        service = TopicService(
            topic_repo=topic_repo,
            uow=uow,
            event_publisher=publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service, topic_repo, uow, publisher

    # ── execute_create_topic ──

    def test_create_topic_happy_path(self) -> None:
        """create_topic debe crear un topic y retornar TopicDetailDTO."""
        service, topic_repo, uow, _ = self._make_service()

        cmd = CreateTopicCommand(name="AI Trends")
        result = service.execute_create_topic(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, TopicDetailDTO)
        assert dto.name == "AI Trends"
        assert dto.is_active is True
        assert dto.description is None

        # Verificar que se guardó en el repo
        assert len(topic_repo._topics) == 1
        assert uow.commit_called is True

    def test_create_topic_with_description(self) -> None:
        """create_topic debe aceptar description."""
        service, topic_repo, _, _ = self._make_service()

        cmd = CreateTopicCommand(name="AI", description="Artificial Intelligence")
        result = service.execute_create_topic(cmd)

        assert result.is_success
        assert result.value.description == "Artificial Intelligence"

    def test_create_topic_duplicate_name(self) -> None:
        """create_topic debe fallar si el nombre ya existe."""
        service, topic_repo, _, _ = self._make_service()

        # Crear primer topic
        cmd1 = CreateTopicCommand(name="AI Trends")
        result1 = service.execute_create_topic(cmd1)
        assert result1.is_success

        # Intentar crear otro con el mismo nombre
        cmd2 = CreateTopicCommand(name="AI Trends")
        result2 = service.execute_create_topic(cmd2)
        assert result2.is_failure
        assert result2.error.code == ApplicationErrorCode.COMMAND_INVALID

    def test_create_topic_empty_name(self) -> None:
        """create_topic debe fallar con nombre vacío (I-22)."""
        service, *_ = self._make_service()

        cmd = CreateTopicCommand(name="")
        result = service.execute_create_topic(cmd)
        assert result.is_failure
        # InvalidTopicError → ErrorMapper maps INVALID_TOPIC → COMMAND_INVALID
        assert result.error.code == ApplicationErrorCode.COMMAND_INVALID

    # ── execute_update_topic ──

    def test_update_topic_happy_path(self) -> None:
        """update_topic debe actualizar campos provistos."""
        service, topic_repo, _, _ = self._make_service()

        # Crear topic
        create_cmd = CreateTopicCommand(name="AI Trends")
        create_result = service.execute_create_topic(create_cmd)
        assert create_result.is_success
        topic_id = create_result.value.id

        # Actualizar
        update_cmd = UpdateTopicCommand(
            topic_id=topic_id,
            name="ML Trends",
            description="Machine Learning",
        )
        result = service.execute_update_topic(update_cmd)
        assert result.is_success
        dto = result.value
        assert dto.name == "ML Trends"
        assert dto.description == "Machine Learning"

    def test_update_topic_not_found(self) -> None:
        """update_topic debe fallar si el topic no existe."""
        service, *_ = self._make_service()

        cmd = UpdateTopicCommand(
            topic_id=_fixed_uuid_str(999),
            name="Nuevo",
        )
        result = service.execute_update_topic(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_update_topic_duplicate_name(self) -> None:
        """update_topic debe fallar si el nuevo nombre ya existe."""
        service, topic_repo, _, _ = self._make_service()

        # Crear dos topics
        service.execute_create_topic(CreateTopicCommand(name="Topic1"))
        create2 = service.execute_create_topic(CreateTopicCommand(name="Topic2"))
        topic2_id = create2.value.id

        # Intentar cambiar Topic2 a nombre de Topic1
        cmd = UpdateTopicCommand(topic_id=topic2_id, name="Topic1")
        result = service.execute_update_topic(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.COMMAND_INVALID

    # ── execute_activate_topic ──

    def test_activate_topic_happy_path(self) -> None:
        """activate_topic debe activar un topic inactivo."""
        service, topic_repo, _, _ = self._make_service()

        # Crear topic
        create_result = service.execute_create_topic(
            CreateTopicCommand(name="Test")
        )
        topic_id = create_result.value.id

        # Desactivar directamente en repo
        topic_repo._topics[topic_id].is_active = False

        # Activar
        cmd = ActivateTopicCommand(topic_id=topic_id)
        result = service.execute_activate_topic(cmd)
        assert result.is_success
        assert result.value.is_active is True

    def test_activate_topic_not_found(self) -> None:
        """activate_topic debe fallar si el topic no existe."""
        service, *_ = self._make_service()

        cmd = ActivateTopicCommand(topic_id=_fixed_uuid_str(999))
        result = service.execute_activate_topic(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_deactivate_topic ──

    def test_deactivate_topic_happy_path(self) -> None:
        """deactivate_topic debe desactivar un topic activo."""
        service, topic_repo, _, _ = self._make_service()

        # Crear topic
        create_result = service.execute_create_topic(
            CreateTopicCommand(name="Test")
        )
        topic_id = create_result.value.id

        # Desactivar
        cmd = DeactivateTopicCommand(topic_id=topic_id)
        result = service.execute_deactivate_topic(cmd)
        assert result.is_success
        assert result.value.is_active is False

    def test_deactivate_topic_not_found(self) -> None:
        """deactivate_topic debe fallar si el topic no existe."""
        service, *_ = self._make_service()

        cmd = DeactivateTopicCommand(topic_id=_fixed_uuid_str(999))
        result = service.execute_deactivate_topic(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_find_topic ──

    def test_find_topic_happy_path(self) -> None:
        """find_topic debe retornar el topic por ID."""
        service, *_ = self._make_service()

        create_result = service.execute_create_topic(
            CreateTopicCommand(name="Test Topic")
        )
        topic_id = create_result.value.id

        query = FindTopicQuery(topic_id=topic_id)
        result = service.execute_find_topic(query)
        assert result.is_success
        assert result.value.name == "Test Topic"

    def test_find_topic_not_found(self) -> None:
        """find_topic debe fallar si no existe."""
        service, *_ = self._make_service()

        query = FindTopicQuery(topic_id=_fixed_uuid_str(999))
        result = service.execute_find_topic(query)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_list_topics ──

    def test_list_topics_empty(self) -> None:
        """list_topics debe retornar lista vacía si no hay topics."""
        service, *_ = self._make_service()

        query = ListTopicsQuery()
        result = service.execute_list_topics(query)
        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 0
        assert len(qr.data) == 0

    def test_list_topics_with_data(self) -> None:
        """list_topics debe listar todos los topics."""
        service, topic_repo, _, _ = self._make_service()

        # Crear dos topics
        service.execute_create_topic(CreateTopicCommand(name="Topic1"))
        service.execute_create_topic(CreateTopicCommand(name="Topic2"))

        query = ListTopicsQuery()
        result = service.execute_list_topics(query)
        assert result.is_success
        qr = result.value
        assert qr.total == 2
        assert len(qr.data) == 2
        assert all(isinstance(d, TopicSummaryDTO) for d in qr.data)
