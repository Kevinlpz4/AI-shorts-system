"""Tests for CategoryService — CRUD, activation, queries for Category."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result

from ingestion.application.commands.category_commands import (
    ActivateCategoryCommand,
    CreateCategoryCommand,
    DeactivateCategoryCommand,
    UpdateCategoryCommand,
)
from ingestion.application.dto.category_dto import CategoryDetailDTO, CategorySummaryDTO
from ingestion.application.mappers.category_mapper import CategoryMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.category_queries import (
    FindCategoryQuery,
    ListCategoriesQuery,
)
from ingestion.application.services.category_service import CategoryService
from ingestion.application.common.query_result import QueryResult
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.domain.entities.category import Category
from ingestion.domain.entities.ids import CategoryId
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.category_name import CategoryName


# ── Mocks ──


class MockCategoryRepository:
    """Mock de CategoryRepository para tests."""

    def __init__(self) -> None:
        self._categories: dict[str, Category] = {}
        self._slugs: set[str] = set()

    def save(self, category: Category) -> None:
        self._categories[str(category.id)] = category
        self._slugs = {c.slug for c in self._categories.values()}

    def find_by_id(self, id: CategoryId) -> Result[Category]:
        key = str(id)
        if key in self._categories:
            return Result.success(self._categories[key])
        return Result.failure(
            Error(
                code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                message=f"Category '{id}' not found",
            )
        )

    def find_by_slug(self, slug: str) -> Result[Category]:
        for c in self._categories.values():
            if c.slug == slug:
                return Result.success(c)
        return Result.failure(
            Error(
                code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                message=f"Category with slug '{slug}' not found",
            )
        )

    def find_all(self) -> list[Category]:
        return list(self._categories.values())

    def find_active(self) -> list[Category]:
        return [c for c in self._categories.values() if c.is_active]

    def find_by_parent(self, parent_id: CategoryId) -> list[Category]:
        return [
            c for c in self._categories.values() if c.parent_id == parent_id
        ]

    def exists_by_slug(self, slug: str) -> bool:
        return slug in self._slugs


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


class TestCategoryService:
    """Suite de tests para CategoryService."""

    def _make_service(
        self,
    ) -> tuple[
        CategoryService,
        MockCategoryRepository,
        MockUnitOfWork,
        MockEventPublisher,
    ]:
        """Crea service con mocks fresh."""
        cat_repo = MockCategoryRepository()
        uow = MockUnitOfWork()
        publisher = MockEventPublisher()
        clock = MockClock()
        uuid_provider = MockUUIDProvider()

        service = CategoryService(
            category_repo=cat_repo,
            uow=uow,
            event_publisher=publisher,
            clock=clock,
            uuid_provider=uuid_provider,
        )
        return service, cat_repo, uow, publisher

    # ── execute_create_category ──

    def test_create_category_happy_path(self) -> None:
        """create_category debe crear una categoría y retornar CategoryDetailDTO."""
        service, cat_repo, uow, _ = self._make_service()

        cmd = CreateCategoryCommand(name="Technology", slug="technology")
        result = service.execute_create_category(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, CategoryDetailDTO)
        assert dto.name == "Technology"
        assert dto.slug == "technology"
        assert dto.is_active is True
        assert dto.parent_id is None

        # Verificar que se guardó en el repo
        assert len(cat_repo._categories) == 1
        assert uow.commit_called is True

    def test_create_category_duplicate_slug(self) -> None:
        """create_category debe fallar si el slug ya existe."""
        service, cat_repo, _, _ = self._make_service()

        # Crear primera categoría
        cmd1 = CreateCategoryCommand(name="Technology", slug="technology")
        result1 = service.execute_create_category(cmd1)
        assert result1.is_success

        # Intentar crear otra con el mismo slug
        cmd2 = CreateCategoryCommand(name="Tech", slug="technology")
        result2 = service.execute_create_category(cmd2)
        assert result2.is_failure
        # DuplicateCategoryNameError → ErrorMapper maps DUPLICATE_CATEGORY_NAME → COMMAND_INVALID
        assert result2.error.code == ApplicationErrorCode.COMMAND_INVALID

    def test_create_category_with_parent(self) -> None:
        """create_category debe aceptar parent_id válido."""
        service, cat_repo, _, _ = self._make_service()

        # Crear categoría padre primero
        parent_cmd = CreateCategoryCommand(name="Root", slug="root")
        parent_result = service.execute_create_category(parent_cmd)
        assert parent_result.is_success
        parent_id = parent_result.value.id

        # Crear subcategoría
        child_cmd = CreateCategoryCommand(
            name="Sub", slug="sub", parent_id=parent_id
        )
        result = service.execute_create_category(child_cmd)
        assert result.is_success
        assert result.value.parent_id == parent_id

    def test_create_category_commit_called(self) -> None:
        """create_category debe llamar a commit en el UoW."""
        service, _, uow, _ = self._make_service()

        cmd = CreateCategoryCommand(name="Test", slug="test")
        result = service.execute_create_category(cmd)
        assert result.is_success
        assert uow.commit_called is True

    # ── execute_update_category ──

    def test_update_category_happy_path(self) -> None:
        """update_category debe actualizar campos provistos."""
        service, cat_repo, _, _ = self._make_service()

        # Crear categoría
        create_cmd = CreateCategoryCommand(name="Technology", slug="technology")
        create_result = service.execute_create_category(create_cmd)
        assert create_result.is_success
        cat_id = create_result.value.id

        # Actualizar
        update_cmd = UpdateCategoryCommand(
            category_id=cat_id,
            name="Tech Updated",
            slug="tech-updated",
        )
        result = service.execute_update_category(update_cmd)
        assert result.is_success
        dto = result.value
        assert dto.name == "Tech Updated"
        assert dto.slug == "tech-updated"

    def test_update_category_not_found(self) -> None:
        """update_category debe fallar si la categoría no existe."""
        service, *_ = self._make_service()

        cmd = UpdateCategoryCommand(
            category_id=_fixed_uuid_str(999),
            name="Nuevo",
        )
        result = service.execute_update_category(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_update_category_duplicate_slug(self) -> None:
        """update_category debe fallar si el nuevo slug ya existe."""
        service, cat_repo, _, _ = self._make_service()

        # Crear dos categorías
        service.execute_create_category(
            CreateCategoryCommand(name="Cat1", slug="cat1")
        )
        create2 = service.execute_create_category(
            CreateCategoryCommand(name="Cat2", slug="cat2")
        )
        cat2_id = create2.value.id

        # Intentar cambiar Cat2 a slug de Cat1
        cmd = UpdateCategoryCommand(category_id=cat2_id, slug="cat1")
        result = service.execute_update_category(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.COMMAND_INVALID

    # ── execute_activate_category ──

    def test_activate_category_happy_path(self) -> None:
        """activate_category debe activar una categoría inactiva."""
        service, cat_repo, _, _ = self._make_service()

        # Crear categoría
        create_result = service.execute_create_category(
            CreateCategoryCommand(name="Test", slug="test")
        )
        cat_id = create_result.value.id

        # Desactivar directamente en repo
        cat_repo._categories[cat_id].is_active = False

        # Activar
        cmd = ActivateCategoryCommand(category_id=cat_id)
        result = service.execute_activate_category(cmd)
        assert result.is_success
        assert result.value.is_active is True

    def test_activate_category_not_found(self) -> None:
        """activate_category debe fallar si la categoría no existe."""
        service, *_ = self._make_service()

        cmd = ActivateCategoryCommand(
            category_id=_fixed_uuid_str(999)
        )
        result = service.execute_activate_category(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_deactivate_category ──

    def test_deactivate_category_happy_path(self) -> None:
        """deactivate_category debe desactivar una categoría activa."""
        service, cat_repo, _, _ = self._make_service()

        # Crear categoría
        create_result = service.execute_create_category(
            CreateCategoryCommand(name="Test", slug="test")
        )
        cat_id = create_result.value.id

        # Desactivar
        cmd = DeactivateCategoryCommand(category_id=cat_id)
        result = service.execute_deactivate_category(cmd)
        assert result.is_success
        assert result.value.is_active is False

    def test_deactivate_category_not_found(self) -> None:
        """deactivate_category debe fallar si la categoría no existe."""
        service, *_ = self._make_service()

        cmd = DeactivateCategoryCommand(
            category_id=_fixed_uuid_str(999)
        )
        result = service.execute_deactivate_category(cmd)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_find_category ──

    def test_find_category_happy_path(self) -> None:
        """find_category debe retornar la categoría por ID."""
        service, *_ = self._make_service()

        create_result = service.execute_create_category(
            CreateCategoryCommand(name="Test", slug="test")
        )
        cat_id = create_result.value.id

        query = FindCategoryQuery(category_id=cat_id)
        result = service.execute_find_category(query)
        assert result.is_success
        assert result.value.name == "Test"
        assert result.value.slug == "test"

    def test_find_category_not_found(self) -> None:
        """find_category debe fallar si no existe."""
        service, *_ = self._make_service()

        query = FindCategoryQuery(
            category_id=_fixed_uuid_str(999)
        )
        result = service.execute_find_category(query)
        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    # ── execute_list_categories ──

    def test_list_categories_empty(self) -> None:
        """list_categories debe retornar lista vacía si no hay categorías."""
        service, *_ = self._make_service()

        query = ListCategoriesQuery()
        result = service.execute_list_categories(query)
        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 0
        assert len(qr.data) == 0

    def test_list_categories_with_data(self) -> None:
        """list_categories debe listar todas las categorías."""
        service, cat_repo, _, _ = self._make_service()

        # Crear dos categorías
        service.execute_create_category(
            CreateCategoryCommand(name="Cat1", slug="cat1")
        )
        service.execute_create_category(
            CreateCategoryCommand(name="Cat2", slug="cat2")
        )

        query = ListCategoriesQuery()
        result = service.execute_list_categories(query)
        assert result.is_success
        qr = result.value
        assert qr.total == 2
        assert len(qr.data) == 2
        assert all(isinstance(d, CategorySummaryDTO) for d in qr.data)
