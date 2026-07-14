"""
Feed API — REST endpoints for Feed CRUD + lifecycle + sync tracking.

Endpoints:
    POST   /api/v1/feeds                                    → Register feed
    GET    /api/v1/feeds/{feed_id}                          → Get feed by ID
    GET    /api/v1/sources/{source_id}/feeds                → List feeds for source
    PUT    /api/v1/feeds/{feed_id}                          → Update feed
    POST   /api/v1/feeds/{feed_id}/activate                 → Activate feed
    POST   /api/v1/feeds/{feed_id}/pause                    → Pause feed
    POST   /api/v1/feeds/{feed_id}/collect                  → Record collection
    POST   /api/v1/feeds/{feed_id}/failure                  → Record failure
    POST   /api/v1/feeds/{feed_id}/categories               → Assign category
    DELETE /api/v1/feeds/{feed_id}/categories/{category_id} → Remove category
    POST   /api/v1/feeds/{feed_id}/topics                   → Assign topic
    DELETE /api/v1/feeds/{feed_id}/topics/{topic_id}        → Remove topic
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from ingestion.presentation.bridge.sync_async import run_sync
from ingestion.presentation.dependencies import get_feed_service, get_uow
from ingestion.presentation.exceptions import (
    map_error_code_to_status,
    problem_response,
)
from ingestion.presentation.schemas.feeds import (
    AssignCategoryRequest,
    AssignTopicRequest,
    FeedDetailResponse,
    FeedSummaryResponse,
    PaginatedFeedsResponse,
    PauseFeedRequest,
    RecordCollectionRequest,
    RecordFailureRequest,
    RegisterFeedRequest,
    UpdateFeedRequest,
)
from ingestion.application.services.feed_service import FeedService
from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
)
from ingestion.application.commands.feed_category_commands import (
    AssignCategoryToFeedCommand,
    AssignTopicToFeedCommand,
)
from ingestion.application.queries.feed_queries import (
    FindFeedQuery,
    ListFeedsQuery,
)
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from ingestion.domain.entities.ids import CategoryId, FeedId, TopicId

router = APIRouter(tags=["Feeds"])


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


async def _handle_no_content(result):
    """Convert a Result to a 204 or error response."""
    if result.is_success:
        return Response(status_code=204)
    return _error_response(result.error)


# ══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/feeds",
    status_code=201,
    summary="Register a new feed",
    operation_id="registerFeed",
)
async def create_feed(
    body: RegisterFeedRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Register a new feed under a news source."""
    result = await run_sync(
        service.execute_register_feed, body.to_command()
    )
    return await _handle_result(result, FeedDetailResponse)


@router.get(
    "/feeds/{feed_id}",
    summary="Get feed by ID",
    operation_id="getFeed",
)
async def get_feed(
    feed_id: str,
    service: FeedService = Depends(get_feed_service),
):
    """Get a feed by its ID."""
    result = await run_sync(
        service.execute_find_feed, FindFeedQuery(feed_id=feed_id)
    )
    return await _handle_result(result, FeedDetailResponse)


@router.get(
    "/sources/{source_id}/feeds",
    summary="List feeds for a source",
    operation_id="listFeedsForSource",
)
async def list_feeds(
    source_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    service: FeedService = Depends(get_feed_service),
):
    """List all feeds for a given news source, with pagination."""
    result = await run_sync(
        service.execute_list_feeds,
        ListFeedsQuery(source_id=source_id, page=page, size=size),
    )
    if result.is_success:
        qr = result.value
        return PaginatedFeedsResponse(
            data=[FeedSummaryResponse.from_dto(d) for d in qr.data],
            meta={
                "total": qr.total,
                "page": qr.page or 1,
                "page_size": qr.size or 50,
            },
        )
    return _error_response(result.error)


@router.put(
    "/feeds/{feed_id}",
    summary="Update feed configuration",
    operation_id="updateFeed",
)
async def update_feed(
    feed_id: str,
    body: UpdateFeedRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Update feed configuration (partial update)."""
    result = await run_sync(
        service.execute_update_feed, body.to_command(feed_id)
    )
    return await _handle_result(result, FeedDetailResponse)


@router.post(
    "/feeds/{feed_id}/activate",
    status_code=204,
    summary="Activate feed",
    operation_id="activateFeed",
)
async def activate_feed(
    feed_id: str,
    service: FeedService = Depends(get_feed_service),
):
    """Activate a previously paused feed."""
    result = await run_sync(
        service.execute_activate_feed,
        ActivateFeedCommand(feed_id=feed_id),
    )
    return await _handle_no_content(result)


@router.post(
    "/feeds/{feed_id}/pause",
    status_code=204,
    summary="Pause feed",
    operation_id="pauseFeed",
)
async def pause_feed(
    feed_id: str,
    body: PauseFeedRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Manually pause a feed."""
    result = await run_sync(
        service.execute_pause_feed,
        PauseFeedCommand(feed_id=feed_id, reason=body.reason),
    )
    return await _handle_no_content(result)


@router.post(
    "/feeds/{feed_id}/collect",
    status_code=204,
    summary="Record successful collection",
    operation_id="recordCollection",
)
async def record_collection(
    feed_id: str,
    body: RecordCollectionRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Record a successful collection from a feed."""
    result = await run_sync(
        service.execute_record_collection,
        RecordCollectionCommand(
            feed_id=feed_id,
            count=body.count,
            batch_id=body.batch_id,
        ),
    )
    return await _handle_no_content(result)


@router.post(
    "/feeds/{feed_id}/failure",
    status_code=204,
    summary="Record feed failure",
    operation_id="recordFailure",
)
async def record_failure(
    feed_id: str,
    body: RecordFailureRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Record a failure from a feed collection attempt."""
    result = await run_sync(
        service.execute_record_failure,
        RecordFailureCommand(feed_id=feed_id, error=body.error),
    )
    return await _handle_no_content(result)


@router.post(
    "/feeds/{feed_id}/categories",
    status_code=204,
    summary="Assign category to feed",
    operation_id="assignCategoryToFeed",
)
async def assign_category(
    feed_id: str,
    body: AssignCategoryRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Assign a category to a feed."""
    result = await run_sync(
        service.execute_assign_category_to_feed,
        AssignCategoryToFeedCommand(
            feed_id=feed_id, category_id=body.category_id
        ),
    )
    return await _handle_no_content(result)


@router.delete(
    "/feeds/{feed_id}/categories/{category_id}",
    status_code=204,
    summary="Remove category from feed",
    operation_id="removeCategoryFromFeed",
)
async def remove_category(
    feed_id: str,
    category_id: str,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
):
    """Remove a category from a feed (uses UoW directly)."""
    with uow:
        result = uow.feeds.find_by_id(FeedId.from_string(feed_id))
        if result.is_failure:
            return _error_response(result.error)
        feed = result.value
        feed.remove_category(CategoryId.from_string(category_id))
        uow.feeds.save(feed)
        uow.commit()
    return Response(status_code=204)


@router.post(
    "/feeds/{feed_id}/topics",
    status_code=204,
    summary="Assign topic to feed",
    operation_id="assignTopicToFeed",
)
async def assign_topic(
    feed_id: str,
    body: AssignTopicRequest,
    service: FeedService = Depends(get_feed_service),
):
    """Assign a topic to a feed."""
    result = await run_sync(
        service.execute_assign_topic_to_feed,
        AssignTopicToFeedCommand(
            feed_id=feed_id, topic_id=body.topic_id
        ),
    )
    return await _handle_no_content(result)


@router.delete(
    "/feeds/{feed_id}/topics/{topic_id}",
    status_code=204,
    summary="Remove topic from feed",
    operation_id="removeTopicFromFeed",
)
async def remove_topic(
    feed_id: str,
    topic_id: str,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
):
    """Remove a topic from a feed (uses UoW directly)."""
    with uow:
        result = uow.feeds.find_by_id(FeedId.from_string(feed_id))
        if result.is_failure:
            return _error_response(result.error)
        feed = result.value
        feed.remove_topic(TopicId.from_string(topic_id))
        uow.feeds.save(feed)
        uow.commit()
    return Response(status_code=204)
