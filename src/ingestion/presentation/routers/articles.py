"""
Article API — REST endpoints for RawArticle CRUD.

Endpoints:
    POST   /api/v1/articles              → Create article
    GET    /api/v1/articles              → List articles (by feed_id query param)
    GET    /api/v1/articles/{article_id} → Get article by ID
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ingestion.presentation.bridge.sync_async import run_sync
from ingestion.presentation.dependencies import get_article_service
from ingestion.presentation.exceptions import (
    map_error_code_to_status,
    problem_response,
)
from ingestion.presentation.schemas.articles import (
    ArticleDetailResponse,
    ArticleSummaryResponse,
    CreateArticleRequest,
    PaginatedArticlesResponse,
)
from ingestion.application.services.article_service import ArticleService
from ingestion.application.queries.article_queries import (
    FindArticleQuery,
    ListArticlesQuery,
)

router = APIRouter(tags=["Articles"])


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
    "/articles",
    status_code=201,
    summary="Create a new article",
)
async def create_article(
    body: CreateArticleRequest,
    service: ArticleService = Depends(get_article_service),
):
    """Create a new raw article."""
    result = await run_sync(
        service.execute_create_article, body.to_command()
    )
    return await _handle_result(result, ArticleDetailResponse)


@router.get(
    "/articles",
    summary="List articles by feed",
)
async def list_articles(
    feed_id: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: ArticleService = Depends(get_article_service),
):
    """List articles for a given feed, with pagination."""
    result = await run_sync(
        service.execute_list_articles,
        ListArticlesQuery(feed_id=feed_id, page=page, size=size),
    )
    if result.is_success:
        qr = result.value
        return PaginatedArticlesResponse(
            data=[ArticleSummaryResponse.from_dto(d) for d in qr.data],
            meta={
                "total": qr.total,
                "page": qr.page or 1,
                "page_size": qr.size or 50,
            },
        )
    return _error_response(result.error)


@router.get(
    "/articles/{article_id}",
    summary="Get article by ID",
)
async def get_article(
    article_id: str,
    service: ArticleService = Depends(get_article_service),
):
    """Get an article by its ID."""
    result = await run_sync(
        service.execute_find_article,
        FindArticleQuery(article_id=article_id),
    )
    return await _handle_result(result, ArticleDetailResponse)
