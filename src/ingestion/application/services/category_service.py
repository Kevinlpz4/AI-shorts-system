"""
CategoryService — Casos de uso para Category.

Orquesta las operaciones CRUD y de estado de la entity Category,
aplicando las reglas de unicidad de slug (I-18) y validación de
jerarquía.

Dependencias inyectadas (DIP):
    - category_repo: CategoryRepository
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort
    - uuid_provider: UUIDProvider

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""

from __future__ import annotations

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.ports.uuid_provider import UUIDProvider
from foundation.result.result import Error, Result

from ingestion.application.dto.category_dto import (
    CategoryDetailDTO,
    CategorySummaryDTO,
)
from ingestion.application.errors.error_mapper import ErrorMapper
from ingestion.application.exceptions.error_code import ApplicationErrorCode
from ingestion.application.mappers.category_mapper import CategoryMapper
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork
from ingestion.application.queries.category_queries import (
    FindCategoryQuery,
    ListCategoriesQuery,
)
from ingestion.application.commands.category_commands import (
    ActivateCategoryCommand,
    CreateCategoryCommand,
    DeactivateCategoryCommand,
    UpdateCategoryCommand,
)
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.entities.category import Category
from ingestion.domain.entities.ids import CategoryId
from ingestion.domain.exceptions import DuplicateCategoryNameError
from ingestion.domain.ports.repositories import CategoryRepository
from ingestion.domain.value_objects.category_name import CategoryName


class CategoryService:
    """Casos de uso para Category.

    Todos los métodos retornan ``Result[CategoryDetailDTO]`` o
    ``Result[QueryResult[CategorySummaryDTO]]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        category_repo: CategoryRepository,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._category_repo = category_repo
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock
        self._uuid_provider = uuid_provider

    # ── Commands ──

    def execute_create_category(
        self, cmd: CreateCategoryCommand
    ) -> Result[CategoryDetailDTO]:
        """Crea una nueva Category.

        Reglas:
            - Verifica unicidad del slug (I-18).
            - Categoría se crea con is_active=True por defecto.
        """
        with self._uow:
            try:
                # Verificar slug único
                if self._category_repo.exists_by_slug(cmd.slug):
                    raise DuplicateCategoryNameError(
                        f"Category slug '{cmd.slug}' already exists"
                    )

                # Parse parent_id si se provee
                parent_id = (
                    CategoryId.from_string(cmd.parent_id)
                    if cmd.parent_id
                    else None
                )

                # Construir entity
                category = Category(
                    id=CategoryId.generate(),
                    name=CategoryName(cmd.name),
                    slug=cmd.slug,
                    parent_id=parent_id,
                )

                self._category_repo.save(category)
                self._uow.commit()

                return Result.success(CategoryMapper.to_detail(category))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_update_category(
        self, cmd: UpdateCategoryCommand
    ) -> Result[CategoryDetailDTO]:
        """Actualiza una Category existente.

        Solo actualiza los campos provistos (no None).
        Verifica unicidad del slug si cambia.
        """
        with self._uow:
            try:
                cat_id = CategoryId.from_string(cmd.category_id)
                result = self._category_repo.find_by_id(cat_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                category = result.value

                if cmd.name is not None:
                    category.name = CategoryName(cmd.name)
                if cmd.slug is not None:
                    # Verificar unicidad si el slug cambia
                    if (
                        cmd.slug != category.slug
                        and self._category_repo.exists_by_slug(cmd.slug)
                    ):
                        raise DuplicateCategoryNameError(
                            f"Category slug '{cmd.slug}' already exists"
                        )
                    category.slug = cmd.slug
                if cmd.parent_id is not None:
                    new_parent = (
                        CategoryId.from_string(cmd.parent_id)
                        if cmd.parent_id
                        else None
                    )
                    category.change_parent(new_parent)

                self._category_repo.save(category)
                self._uow.commit()

                return Result.success(CategoryMapper.to_detail(category))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_activate_category(
        self, cmd: ActivateCategoryCommand
    ) -> Result[CategoryDetailDTO]:
        """Activa una Category."""
        with self._uow:
            try:
                cat_id = CategoryId.from_string(cmd.category_id)
                result = self._category_repo.find_by_id(cat_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                category = result.value

                category.activate()
                self._category_repo.save(category)
                self._uow.commit()

                return Result.success(CategoryMapper.to_detail(category))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_deactivate_category(
        self, cmd: DeactivateCategoryCommand
    ) -> Result[CategoryDetailDTO]:
        """Desactiva una Category.

        NOTA: El cascade a subcategorías (I-21) es regla de Application Layer.
        Por ahora, desactivación simple. Cascade se puede agregar después.
        """
        with self._uow:
            try:
                cat_id = CategoryId.from_string(cmd.category_id)
                result = self._category_repo.find_by_id(cat_id)
                if result.is_failure:
                    return Result.failure(
                        ErrorMapper.map_result_error(result.error)
                    )
                category = result.value

                category.deactivate()
                self._category_repo.save(category)
                self._uow.commit()

                return Result.success(CategoryMapper.to_detail(category))

            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    # ── Queries (solo lectura, sin UoW) ──

    def execute_find_category(
        self, query: FindCategoryQuery
    ) -> Result[CategoryDetailDTO]:
        """Busca una Category por ID.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            cat_id = CategoryId.from_string(query.category_id)
            result = self._category_repo.find_by_id(cat_id)
            if result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(result.error)
                )
            return Result.success(CategoryMapper.to_detail(result.value))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )

    def execute_list_categories(
        self, query: ListCategoriesQuery
    ) -> Result[QueryResult[CategorySummaryDTO]]:
        """Lista todas las Categories.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            categories = self._category_repo.find_all()
            dtos = [CategoryMapper.to_summary(c) for c in categories]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=len(dtos),
                    page=query.page,
                    size=query.size,
                )
            )
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )
