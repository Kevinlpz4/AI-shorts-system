"""
Source Intelligence router — GET /source-quality/{source}.

Returns comprehensive quality intelligence for a news source:
approval rate, confidence, trend, and keyword effectiveness.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.responses import KeywordStatResponse, SourceQualityResponse

router = APIRouter()


def _profile_to_response(
    profile: object,
    confidence: float = 0.0,
    trend: str = "STABLE",
) -> SourceQualityResponse:
    """Convert a SourceQualityProfile entity to a response model.

    Args:
        profile: SourceQualityProfile domain entity.
        confidence: Computed confidence value.
        trend: Trend direction string.

    Returns:
        SourceQualityResponse Pydantic model.
    """
    keywords = [
        KeywordStatResponse(
            keyword=kw.keyword,
            count=kw.count,
            approved_count=kw.approved_count,
            approval_rate=kw.approval_rate,
        )
        for kw in profile.keywords.values()  # type: ignore[union-attr]
    ]

    return SourceQualityResponse(
        source_name=profile.source_name,  # type: ignore[union-attr]
        approval_rate=profile.approval_rate,  # type: ignore[union-attr]
        total_decisions=profile.total_decisions,  # type: ignore[union-attr]
        approved_count=profile.approved_count,  # type: ignore[union-attr]
        rejected_count=profile.rejected_count,  # type: ignore[union-attr]
        confidence=confidence,
        trend=trend,
        keywords=keywords,
    )


@router.get(
    "/source-quality/{source}",
    response_model=SourceQualityResponse,
    summary="Get source quality intelligence",
)
async def source_quality(
    source: str,
    services: ServiceDependencies = Depends(get_services),
) -> SourceQualityResponse:
    """Get comprehensive quality intelligence for a news source.

    Returns approval rate, confidence, trend, and keyword effectiveness.
    """
    result = services.source_quality_repo.find_by_source_name(source)
    if result.is_failure:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails(
                type="about:blank",
                title="Source Not Found",
                status=404,
                detail=f"Source '{source}' not found in knowledge base",
            ).model_dump(),
        )

    profile = result.value
    # Confidence from sample size (30+ decisions = full confidence)
    confidence = min(1.0, profile.total_decisions / 30) if profile.total_decisions > 0 else 0.0

    return _profile_to_response(profile, confidence=confidence, trend="STABLE")
