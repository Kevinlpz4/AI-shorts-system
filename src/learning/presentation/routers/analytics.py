"""
Analytics router — GET /analytics.

Returns comprehensive learning analytics:
feedback totals, approval ratio, learning progress,
dataset count, signal distribution, and source ranking.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.responses import AnalyticsResponse, SourceQualityResponse, KeywordStatResponse
from learning.application.queries.analytics_queries import GetAnalyticsQuery

router = APIRouter()


def _source_quality_to_response(source_dto: object) -> SourceQualityResponse:
    """Convert a SourceQualityDTO to a response model."""
    keyword_stats = [
        KeywordStatResponse(
            keyword=kw.keyword,
            count=kw.count,
            approved_count=kw.approved_count,
            approval_rate=kw.approval_rate,
        )
        for kw in getattr(source_dto, "keyword_stats", ())
    ]
    total = getattr(source_dto, "total_decisions", 0)
    confidence = min(1.0, total / 30) if total > 0 else 0.0

    return SourceQualityResponse(
        source_name=source_dto.source_name,  # type: ignore[union-attr]
        approval_rate=source_dto.approval_rate,  # type: ignore[union-attr]
        total_decisions=total,
        approved_count=source_dto.approved,  # type: ignore[union-attr]
        rejected_count=source_dto.rejected,  # type: ignore[union-attr]
        confidence=confidence,
        trend="STABLE",
        keywords=keyword_stats,
    )


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get learning analytics",
)
async def analytics(
    services: ServiceDependencies = Depends(get_services),
) -> AnalyticsResponse:
    """Get comprehensive learning analytics.

    Returns feedback totals, approval ratio, learning progress,
    dataset count, signal distribution, and source ranking.
    """
    query = GetAnalyticsQuery()
    result = services.analytics_service.execute_get_analytics(query)
    if result.is_failure:
        code = result.error.code
        title_str = code.value if hasattr(code, "value") else str(code)
        raise HTTPException(
            status_code=500,
            detail=ProblemDetails(
                type="about:blank",
                title=title_str,
                status=500,
                detail=result.error.message or "Analytics query failed",
            ).model_dump(),
        )

    dto = result.value
    return AnalyticsResponse(
        total_feedback=dto.total_feedback,
        approval_ratio=dto.average_approval_rate,
        total_signals=dto.total_signals,
        signals_by_dimension=dto.signals_by_dimension,
        average_approval_rate=dto.average_approval_rate,
        top_sources=[_source_quality_to_response(s) for s in dto.top_sources],
        model_version="current",
    )
