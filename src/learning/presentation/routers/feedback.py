"""
Feedback router — POST /feedback.

Records a human decision on content.
Creates a new immutable FeedbackRecord. Never modifies history.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.requests import FeedbackRequest
from learning.presentation.schemas.responses import FeedbackResponse

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Record human feedback",
)
async def record_feedback(
    request: FeedbackRequest,
    services: ServiceDependencies = Depends(get_services),
) -> FeedbackResponse:
    """Record a human decision on content.

    Creates a new immutable FeedbackRecord. Never modifies history.
    The feature_snapshot is passed as features dict to the command;
    the service constructs the FeatureSnapshot internally.
    """
    command = RecordFeedbackCommand(
        topic_id=request.topic_id,
        decision=request.decision,
        reason=request.reason,
        source_name=request.source_name,
        title=request.title,
        features=request.feature_snapshot,
    )

    result = services.decision_service.execute_record_feedback(command)
    if result.is_failure:
        code = result.error.code
        status = 404 if "NOT_FOUND" in str(code) else 422
        title_str = code.value if hasattr(code, "value") else str(code)
        raise HTTPException(
            status_code=status,
            detail=ProblemDetails(
                type="about:blank",
                title=title_str,
                status=status,
                detail=result.error.message or "Feedback recording failed",
            ).model_dump(),
        )

    dto = result.value
    return FeedbackResponse(
        feedback_id=dto.id,
        topic_id=dto.topic_id,
        decision=dto.decision,
        captured_at=dto.created_at,
        message="Feedback recorded successfully",
    )
