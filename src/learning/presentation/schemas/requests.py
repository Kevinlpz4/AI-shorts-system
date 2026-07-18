"""
Request Pydantic models for the Learning Intelligence API.

All incoming request bodies are validated against these models.
Completely separate from domain entities and DTOs.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request body for predicting content approval.

    Attributes:
        source_name: Name of the content source (e.g., "reuters").
        title: Optional title of the content.
        features: Optional scoring features (e.g., {"final_score": 0.75}).
    """

    source_name: str = Field(..., min_length=1, examples=["reuters"])
    title: str = Field(default="", examples=["Breaking news about AI"])
    features: dict[str, float] | None = Field(
        default=None, examples=[{"final_score": 0.75}]
    )


class RecommendationRequest(BaseModel):
    """Request body for generating an editorial recommendation.

    Attributes:
        source_name: Name of the content source.
        title: Optional title of the content.
        features: Optional scoring features.
    """

    source_name: str = Field(..., min_length=1, examples=["reuters"])
    title: str = Field(default="", examples=["Breaking news about AI"])
    features: dict[str, float] | None = None


class FeedbackRequest(BaseModel):
    """Request body for recording human feedback on content.

    Attributes:
        topic_id: ID of the topic from Ingestion BC.
        decision: Type of decision made by the human.
        reason: Optional reason (required for rejections).
        source_name: Name of the content source.
        title: Title of the content.
        feature_snapshot: Optional snapshot of scoring features.
        score_snapshot: Optional snapshot of score components.
    """

    topic_id: str = Field(..., min_length=1)
    decision: str = Field(
        ...,
        pattern="^(APPROVED|REJECTED|AUTO_APPROVED|AUTO_REJECTED|OVERRIDDEN)$",
    )
    reason: str | None = None
    source_name: str = Field(..., min_length=1)
    title: str = Field(default="")
    feature_snapshot: dict[str, float] | None = None
    score_snapshot: dict[str, float] | None = None


class DatasetExportRequest(BaseModel):
    """Request body for exporting a new dataset version.

    Attributes:
        format: Export format (JSONL or CSV).
        decision_filter: Optional filter by decision type.
        min_score: Optional minimum score filter.
        max_score: Optional maximum score filter.
    """

    format: str = Field(default="JSONL", pattern="^(JSONL|CSV)$")
    decision_filter: str | None = Field(
        default=None, pattern="^(APPROVED|REJECTED)$"
    )
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    max_score: float | None = Field(default=None, ge=0.0, le=1.0)
