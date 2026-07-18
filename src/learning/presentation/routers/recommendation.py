"""
Recommendation router — POST /recommend.

Generates editorial recommendations: APPROVE, REJECT, or MANUAL_REVIEW.
Each recommendation includes reasoning based on accumulated knowledge.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.requests import RecommendationRequest
from learning.presentation.schemas.responses import RecommendationResponse

router = APIRouter()


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Generate editorial recommendation",
)
async def recommend(
    request: RecommendationRequest,
    services: ServiceDependencies = Depends(get_services),
) -> RecommendationResponse:
    """Generate an editorial recommendation: APPROVE, REJECT, or MANUAL_REVIEW.

    Each recommendation includes reasoning based on accumulated knowledge.
    """
    result = services.recommendation_service.recommend(
        source_name=request.source_name,
        features=request.features,
    )
    if result.is_failure:
        code = result.error.code
        status = 404 if "NOT_FOUND" in str(code) else 422
        title = code.value if hasattr(code, "value") else str(code)
        raise HTTPException(
            status_code=status,
            detail=ProblemDetails(
                type="about:blank",
                title=title,
                status=status,
                detail=result.error.message or "Recommendation failed",
            ).model_dump(),
        )

    dto = result.value
    return RecommendationResponse(
        recommendation=dto.recommendation,
        probability=dto.probability,
        confidence=dto.confidence,
        reasoning=list(dto.reasoning),
        source_quality=dto.source_quality,
        model_version=dto.model_version,
    )
