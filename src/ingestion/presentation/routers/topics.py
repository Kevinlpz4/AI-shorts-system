"""
Topic API — REST endpoints for Topic CRUD + lifecycle.

Endpoints:
    POST   /api/v1/topics              → Create topic
    GET    /api/v1/topics              → List all topics
    GET    /api/v1/topics/{topic_id}   → Get topic by ID
    PUT    /api/v1/topics/{topic_id}   → Update topic
    POST   /api/v1/topics/{topic_id}/activate   → Activate topic
    POST   /api/v1/topics/{topic_id}/deactivate → Deactivate topic
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ingestion.presentation.bridge.sync_async import run_sync
from ingestion.presentation.dependencies import get_topic_service
from ingestion.presentation.exceptions import (
    map_error_code_to_status,
    problem_response,
)
from ingestion.presentation.schemas.topics import (
    CreateTopicRequest,
    PaginatedTopicsResponse,
    TopicDetailResponse,
    TopicSummaryResponse,
    UpdateTopicRequest,
)
from ingestion.application.services.topic_service import TopicService
from ingestion.application.commands.topic_commands import (
    ActivateTopicCommand,
    DeactivateTopicCommand,
)
from ingestion.application.queries.topic_queries import (
    FindTopicQuery,
    ListTopicsQuery,
)

router = APIRouter(tags=["Topics"])


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
    "/topics",
    status_code=201,
    summary="Create a new topic",
)
async def create_topic(
    body: CreateTopicRequest,
    service: TopicService = Depends(get_topic_service),
):
    """Create a new topic."""
    result = await run_sync(
        service.execute_create_topic, body.to_command()
    )
    return await _handle_result(result, TopicDetailResponse)


@router.get(
    "/topics",
    summary="List all topics",
)
async def list_topics(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: TopicService = Depends(get_topic_service),
):
    """List all topics with pagination."""
    result = await run_sync(
        service.execute_list_topics,
        ListTopicsQuery(page=page, size=size),
    )
    if result.is_success:
        qr = result.value
        return PaginatedTopicsResponse(
            data=[TopicSummaryResponse.from_dto(d) for d in qr.data],
            meta={
                "total": qr.total,
                "page": qr.page or 1,
                "page_size": qr.size or 50,
            },
        )
    return _error_response(result.error)


@router.get(
    "/topics/{topic_id}",
    summary="Get topic by ID",
)
async def get_topic(
    topic_id: str,
    service: TopicService = Depends(get_topic_service),
):
    """Get a topic by its ID."""
    result = await run_sync(
        service.execute_find_topic,
        FindTopicQuery(topic_id=topic_id),
    )
    return await _handle_result(result, TopicDetailResponse)


@router.put(
    "/topics/{topic_id}",
    summary="Update topic",
)
async def update_topic(
    topic_id: str,
    body: UpdateTopicRequest,
    service: TopicService = Depends(get_topic_service),
):
    """Update a topic (partial update)."""
    result = await run_sync(
        service.execute_update_topic, body.to_command(topic_id)
    )
    return await _handle_result(result, TopicDetailResponse)


@router.post(
    "/topics/{topic_id}/activate",
    summary="Activate topic",
)
async def activate_topic(
    topic_id: str,
    service: TopicService = Depends(get_topic_service),
):
    """Activate a topic."""
    result = await run_sync(
        service.execute_activate_topic,
        ActivateTopicCommand(topic_id=topic_id),
    )
    return await _handle_result(result, TopicDetailResponse)


@router.post(
    "/topics/{topic_id}/deactivate",
    summary="Deactivate topic",
)
async def deactivate_topic(
    topic_id: str,
    service: TopicService = Depends(get_topic_service),
):
    """Deactivate a topic."""
    result = await run_sync(
        service.execute_deactivate_topic,
        DeactivateTopicCommand(topic_id=topic_id),
    )
    return await _handle_result(result, TopicDetailResponse)
