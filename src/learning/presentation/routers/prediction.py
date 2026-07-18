"""
Prediction router — POST /predict.

Predicts whether content from a source will be approved.
Uses statistical signals, accumulated knowledge, and current model weights.
No AI — pure statistical prediction based on historical data.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.requests import PredictionRequest
from learning.presentation.schemas.responses import PredictionResponse
from learning.application.queries.prediction_queries import PredictApprovalQuery

router = APIRouter()


def _map_error_to_problem_details(code: object, message: str) -> dict:
    """Map an application error to RFC 9457 ProblemDetails dict."""
    from learning.application.exceptions.error_code import ApplicationErrorCode

    status_map = {
        ApplicationErrorCode.RESOURCE_NOT_FOUND: 404,
        ApplicationErrorCode.COMMAND_INVALID: 422,
        ApplicationErrorCode.COMMAND_MISSING_FIELD: 422,
        ApplicationErrorCode.OPERATION_FAILED: 500,
        ApplicationErrorCode.TRANSACTION_FAILED: 500,
        ApplicationErrorCode.CONCURRENCY_CONFLICT: 409,
    }
    status = status_map.get(code, 500)  # type: ignore[arg-type]
    title = code.value if hasattr(code, "value") else str(code)  # type: ignore[union-attr]
    return ProblemDetails(
        type="about:blank",
        title=title,
        status=status,
        detail=message or "An error occurred",
    ).model_dump()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict content approval",
)
async def predict(
    request: PredictionRequest,
    services: ServiceDependencies = Depends(get_services),
) -> PredictionResponse:
    """Predict whether content from a source will be approved.

    Uses statistical signals, accumulated knowledge, and current model weights.
    No AI — pure statistical prediction based on historical data.
    """
    query = PredictApprovalQuery(
        source_name=request.source_name,
        features=request.features,
    )
    result = services.prediction_service.execute_predict_approval(query)
    if result.is_failure:
        raise HTTPException(
            status_code=422,
            detail=_map_error_to_problem_details(
                result.error.code, result.error.message
            ),
        )
    dto = result.value
    # Map probability to recommendation
    if dto.probability >= 0.7:
        recommendation = "APPROVE"
    elif dto.probability < 0.3:
        recommendation = "REJECT"
    else:
        recommendation = "MANUAL_REVIEW"

    return PredictionResponse(
        recommendation=recommendation,
        score=dto.probability,
        confidence=dto.confidence,
        explanation=dto.reasoning_summary,
        model_version="current",
    )
