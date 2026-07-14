"""
Source API — REST endpoints for NewsSource CRUD + lifecycle.

Endpoints:
    POST   /api/v1/sources                         → Register source
    GET    /api/v1/sources                         → List active sources
    GET    /api/v1/sources/{source_id}             → Get source by ID
    PUT    /api/v1/sources/{source_id}             → Update source
    POST   /api/v1/sources/{source_id}/activate    → Activate source
    POST   /api/v1/sources/{source_id}/deactivate  → Deactivate source
    POST   /api/v1/sources/{source_id}/categories  → Assign category
    DELETE /api/v1/sources/{source_id}/categories/{category_id} → Remove category
    POST   /api/v1/sources/{source_id}/topics      → Assign topic
    DELETE /api/v1/sources/{source_id}/topics/{topic_id}       → Remove topic
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ingestion.presentation.bridge.sync_async import run_sync
from ingestion.presentation.dependencies import get_source_service, get_uow
from ingestion.presentation.exceptions import (
    map_error_code_to_status,
    problem_response,
)
from ingestion.presentation.schemas.sources import (
    AssignCategoryRequest,
    AssignTopicRequest,
    DeactivateSourceRequest,
    PaginatedSourcesResponse,
    RegisterSourceRequest,
    SourceDetailResponse,
    SourceSummaryResponse,
    UpdateSourceRequest,
)
from ingestion.application.services.source_service import SourceService
from ingestion.application.commands.source_commands import (
    DisableSourceCommand,
    EnableSourceCommand,
)
from ingestion.application.commands.source_category_commands import (
    AssignCategoryToSourceCommand,
    AssignTopicToSourceCommand,
)
from ingestion.application.queries.source_queries import (
    FindSourceQuery,
    ListActiveSourcesQuery,
)
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from ingestion.domain.entities.ids import CategoryId, SourceId, TopicId

router = APIRouter(tags=["Sources"])


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
    """Convert a Result to an HTTP response. Raises on failure."""
    if result.is_success:
        return response_model_cls.from_dto(result.value)
    return _error_response(result.error)


async def _handle_no_content(result):
    """Convert a Result to a 204 or error response."""
    if result.is_success:
        return Response(status_code=204)
    return _error_response(result.error)


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/sources",
    status_code=201,
    summary="Register a new news source",
)
async def create_source(
    body: RegisterSourceRequest,
    service: SourceService = Depends(get_source_service),
):
    """Register a new news source."""
    result = await run_sync(
        service.execute_register_source, body.to_command()
    )
    return await _handle_result(result, SourceDetailResponse)


@router.get(
    "/sources",
    summary="List all active sources",
)
async def list_sources(
    service: SourceService = Depends(get_source_service),
):
    """List all active sources."""
    result = await run_sync(
        service.execute_list_active_sources, ListActiveSourcesQuery()
    )
    if result.is_success:
        qr = result.value
        return PaginatedSourcesResponse(
            data=[SourceSummaryResponse.from_dto(d) for d in qr.data],
            meta={
                "total": qr.total,
                "page": qr.page or 1,
                "page_size": qr.size or 20,
            },
        )
    return _error_response(result.error)


@router.get(
    "/sources/{source_id}",
    summary="Get source by ID",
)
async def get_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
):
    """Get source by ID."""
    result = await run_sync(
        service.execute_find_source, FindSourceQuery(source_id=source_id)
    )
    return await _handle_result(result, SourceDetailResponse)


@router.put(
    "/sources/{source_id}",
    summary="Update source",
)
async def update_source(
    source_id: str,
    body: UpdateSourceRequest,
    service: SourceService = Depends(get_source_service),
):
    """Update source."""
    result = await run_sync(
        service.execute_update_source, body.to_command(source_id)
    )
    return await _handle_result(result, SourceDetailResponse)


@router.post(
    "/sources/{source_id}/activate",
    summary="Activate source",
)
async def activate_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
):
    """Activate source."""
    result = await run_sync(
        service.execute_enable_source,
        EnableSourceCommand(source_id=source_id),
    )
    return await _handle_result(result, SourceDetailResponse)


@router.post(
    "/sources/{source_id}/deactivate",
    summary="Deactivate source",
)
async def deactivate_source(
    source_id: str,
    body: DeactivateSourceRequest,
    service: SourceService = Depends(get_source_service),
):
    """Deactivate source."""
    result = await run_sync(
        service.execute_disable_source,
        DisableSourceCommand(source_id=source_id, reason=body.reason),
    )
    return await _handle_result(result, SourceDetailResponse)


@router.post(
    "/sources/{source_id}/categories",
    status_code=204,
    summary="Assign category to source",
)
async def assign_category(
    source_id: str,
    body: AssignCategoryRequest,
    service: SourceService = Depends(get_source_service),
):
    """Assign category to source."""
    result = await run_sync(
        service.execute_assign_category_to_source,
        AssignCategoryToSourceCommand(
            source_id=source_id, category_id=body.category_id
        ),
    )
    return await _handle_no_content(result)


@router.delete(
    "/sources/{source_id}/categories/{category_id}",
    status_code=204,
    summary="Remove category from source",
)
async def remove_category(
    source_id: str,
    category_id: str,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
):
    """Remove category from source (uses UoW directly)."""
    with uow:
        result = uow.news_sources.find_by_id(
            SourceId.from_string(source_id)
        )
        if result.is_failure:
            return _error_response(result.error)
        source = result.value
        source.remove_category(CategoryId.from_string(category_id))
        uow.news_sources.save(source)
        uow.commit()
    return Response(status_code=204)


@router.post(
    "/sources/{source_id}/topics",
    status_code=204,
    summary="Assign topic to source",
)
async def assign_topic(
    source_id: str,
    body: AssignTopicRequest,
    service: SourceService = Depends(get_source_service),
):
    """Assign topic to source."""
    result = await run_sync(
        service.execute_assign_topic_to_source,
        AssignTopicToSourceCommand(
            source_id=source_id, topic_id=body.topic_id
        ),
    )
    return await _handle_no_content(result)


@router.delete(
    "/sources/{source_id}/topics/{topic_id}",
    status_code=204,
    summary="Remove topic from source",
)
async def remove_topic(
    source_id: str,
    topic_id: str,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
):
    """Remove topic from source (uses UoW directly)."""
    with uow:
        result = uow.news_sources.find_by_id(
            SourceId.from_string(source_id)
        )
        if result.is_failure:
            return _error_response(result.error)
        source = result.value
        source.remove_topic(TopicId.from_string(topic_id))
        uow.news_sources.save(source)
        uow.commit()
    return Response(status_code=204)
