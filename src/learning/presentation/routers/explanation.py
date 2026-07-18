"""
Explanation router — GET /explain/{article_id}.

Explains why an article received its score.
Shows signals used, weights, confidence, positive and negative factors.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.responses import ExplanationResponse

router = APIRouter()


@router.get(
    "/explain/{article_id}",
    response_model=ExplanationResponse,
    summary="Explain article score",
)
async def explain(
    article_id: str,
    services: ServiceDependencies = Depends(get_services),
) -> ExplanationResponse:
    """Explain why an article received its score.

    Shows signals used, weights, confidence, positive and negative factors.
    Uses the article_id as source_name for explanation lookup.
    """
    result = services.explanation_service.explain_decision(
        source_name=article_id,
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
                detail=result.error.message or "Explanation failed",
            ).model_dump(),
        )

    dto = result.value

    # Classify positive/negative factors
    positive: list[str] = []
    negative: list[str] = []

    if dto.source_bonus > 0.5:
        positive.append(f"High source quality: {dto.source_bonus:.2f}")
    elif dto.source_bonus > 0.0:
        positive.append(f"Moderate source quality: {dto.source_bonus:.2f}")
    else:
        negative.append(f"Low source quality: {dto.source_bonus:.2f}")

    if dto.keyword_bonus > 0.3:
        positive.append(f"Strong keyword match: {dto.keyword_bonus:.2f}")
    elif dto.keyword_bonus > 0.0:
        positive.append(f"Weak keyword match: {dto.keyword_bonus:.2f}")

    if dto.topic_penalty > 0.3:
        negative.append(f"Topic mismatch penalty: {dto.topic_penalty:.2f}")

    if dto.freshness_score > 0.5:
        positive.append(f"Good freshness: {dto.freshness_score:.2f}")

    return ExplanationResponse(
        source_name=dto.source_name,
        base_score=dto.base_score,
        freshness_score=dto.freshness_score,
        keyword_bonus=dto.keyword_bonus,
        source_bonus=dto.source_bonus,
        topic_penalty=dto.topic_penalty,
        confidence=dto.confidence,
        final_score=dto.final_score,
        model_version=dto.model_version,
        active_signals=list(dto.active_signals),
        positive_factors=positive,
        negative_factors=negative,
    )
