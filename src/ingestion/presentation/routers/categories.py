"""
Category API — REST endpoints for Category CRUD + lifecycle.

Endpoints:
    POST   /api/v1/categories              → Create category
    GET    /api/v1/categories              → List all categories
    GET    /api/v1/categories/{category_id} → Get category by ID
    PUT    /api/v1/categories/{category_id} → Update category
    POST   /api/v1/categories/{category_id}/activate   → Activate category
    POST   /api/v1/categories/{category_id}/deactivate → Deactivate category
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ingestion.presentation.bridge.sync_async import run_sync
from ingestion.presentation.dependencies import get_category_service
from ingestion.presentation.exceptions import (
    map_error_code_to_status,
    problem_response,
)
from ingestion.presentation.schemas.categories import (
    CategoryDetailResponse,
    CategorySummaryResponse,
    CreateCategoryRequest,
    PaginatedCategoriesResponse,
    UpdateCategoryRequest,
)
from ingestion.application.services.category_service import CategoryService
from ingestion.application.commands.category_commands import (
    ActivateCategoryCommand,
    DeactivateCategoryCommand,
)
from ingestion.application.queries.category_queries import (
    FindCategoryQuery,
    ListCategoriesQuery,
)

router = APIRouter(tags=["Categories"])


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _error_response(error: object) -> object:
    """Convert an Error object to an RFC 9457 Problem Details response."""
    code_str = (
        error.code.value if hasattr(error.code, "value") else str(error.code)
    )
    status = map_error_code_to_status(code_str)
    return problem_response(
        status=status,
        type_uri=f"https://api.ai-shorts.dev/errors/{code_str}",
        title=error.code.name if hasattr(error.code, "name") else "Error",
        detail=error.message,
        error_code=code_str,
    )


async def _handle_result(result, response_model_cls):
    """Convert a Result to an HTTP response."""
    if result.is_success:
        return response_model_cls.from_dto(result.value)
    return _error_response(result.error)


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/categories",
    status_code=201,
    summary="Create a new category",
)
async def create_category(
    body: CreateCategoryRequest,
    service: CategoryService = Depends(get_category_service),
):
    """Create a new category."""
    result = await run_sync(
        service.execute_create_category, body.to_command()
    )
    return await _handle_result(result, CategoryDetailResponse)


@router.get(
    "/categories",
    summary="List all categories",
)
async def list_categories(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: CategoryService = Depends(get_category_service),
):
    """List all categories with pagination."""
    result = await run_sync(
        service.execute_list_categories,
        ListCategoriesQuery(page=page, size=size),
    )
    if result.is_success:
        qr = result.value
        return PaginatedCategoriesResponse(
            data=[CategorySummaryResponse.from_dto(d) for d in qr.data],
            meta={
                "total": qr.total,
                "page": qr.page or 1,
                "page_size": qr.size or 50,
            },
        )
    return _error_response(result.error)


@router.get(
    "/categories/{category_id}",
    summary="Get category by ID",
)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
):
    """Get a category by its ID."""
    result = await run_sync(
        service.execute_find_category,
        FindCategoryQuery(category_id=category_id),
    )
    return await _handle_result(result, CategoryDetailResponse)


@router.put(
    "/categories/{category_id}",
    summary="Update category",
)
async def update_category(
    category_id: str,
    body: UpdateCategoryRequest,
    service: CategoryService = Depends(get_category_service),
):
    """Update a category (partial update)."""
    result = await run_sync(
        service.execute_update_category, body.to_command(category_id)
    )
    return await _handle_result(result, CategoryDetailResponse)


@router.post(
    "/categories/{category_id}/activate",
    summary="Activate category",
)
async def activate_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
):
    """Activate a category."""
    result = await run_sync(
        service.execute_activate_category,
        ActivateCategoryCommand(category_id=category_id),
    )
    return await _handle_result(result, CategoryDetailResponse)


@router.post(
    "/categories/{category_id}/deactivate",
    summary="Deactivate category",
)
async def deactivate_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
):
    """Deactivate a category."""
    result = await run_sync(
        service.execute_deactivate_category,
        DeactivateCategoryCommand(category_id=category_id),
    )
    return await _handle_result(result, CategoryDetailResponse)
