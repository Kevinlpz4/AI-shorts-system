"""
Response Pydantic models for the Learning Intelligence API.

All outgoing responses are serialized through these models.
Completely separate from domain entities and DTOs.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response for a prediction request.

    Attributes:
        recommendation: Predicted recommendation (APPROVE, REJECT, MANUAL_REVIEW).
        score: Predicted probability of approval (0.0-1.0).
        confidence: Confidence in the prediction (0.0-1.0).
        explanation: Human-readable reasoning summary.
        model_version: Version of the model used.
    """

    recommendation: str
    score: float
    confidence: float
    explanation: str
    model_version: str


class ExplanationResponse(BaseModel):
    """Response for an explanation request.

    Attributes:
        source_name: Name of the source being explained.
        base_score: Base content quality score.
        freshness_score: Time-based freshness score.
        keyword_bonus: Bonus from keyword matching.
        source_bonus: Bonus from source reliability.
        topic_penalty: Penalty from topic mismatch.
        confidence: Confidence in the scoring.
        final_score: Computed final score.
        model_version: Version of the model used.
        active_signals: List of active signals that influenced the score.
        positive_factors: Factors that increased the score.
        negative_factors: Factors that decreased the score.
    """

    source_name: str
    base_score: float
    freshness_score: float
    keyword_bonus: float
    source_bonus: float
    topic_penalty: float
    confidence: float
    final_score: float
    model_version: str
    active_signals: list[str]
    positive_factors: list[str]
    negative_factors: list[str]


class RecommendationResponse(BaseModel):
    """Response for a recommendation request.

    Attributes:
        recommendation: Editorial recommendation (APPROVE, REJECT, MANUAL_REVIEW).
        probability: Predicted probability of approval.
        confidence: Confidence in the recommendation.
        reasoning: List of reasons supporting the recommendation.
        source_quality: Accumulated quality rate of the source.
        model_version: Version of the algorithm used.
    """

    recommendation: str
    probability: float
    confidence: float
    reasoning: list[str]
    source_quality: float
    model_version: str


class FeedbackResponse(BaseModel):
    """Response for a feedback recording request.

    Attributes:
        feedback_id: Unique ID of the recorded feedback.
        topic_id: Topic identifier.
        decision: Type of decision recorded.
        captured_at: Timestamp when feedback was captured.
        message: Confirmation message.
    """

    feedback_id: str
    topic_id: str
    decision: str
    captured_at: str
    message: str


class KeywordStatResponse(BaseModel):
    """Statistics for a single keyword.

    Attributes:
        keyword: The keyword being tracked.
        count: Total number of appearances.
        approved_count: Number of approved appearances.
        approval_rate: Approval rate for this keyword.
    """

    keyword: str
    count: int
    approved_count: int
    approval_rate: float


class SourceQualityResponse(BaseModel):
    """Quality intelligence for a content source.

    Attributes:
        source_name: Name of the source.
        approval_rate: Rate of approvals (0.0-1.0).
        total_decisions: Total number of decisions.
        approved_count: Number of approvals.
        rejected_count: Number of rejections.
        confidence: Confidence based on sample size.
        trend: Trend direction (IMPROVING, DECLINING, STABLE).
        keywords: Per-keyword effectiveness statistics.
    """

    source_name: str
    approval_rate: float
    total_decisions: int
    approved_count: int
    rejected_count: int
    confidence: float
    trend: str
    keywords: list[KeywordStatResponse]


class KnowledgeResponse(BaseModel):
    """Summary of all accumulated knowledge.

    Attributes:
        top_sources: Sources with highest approval rates.
        top_keywords: Most frequently appearing keywords.
        top_categories: Most frequently appearing categories.
        top_topics: Most frequently appearing topics.
        active_signals_count: Total number of active signals.
        knowledge_coverage: Coverage ratio (0.0-1.0).
        model_version: Current model version.
    """

    top_sources: list[SourceQualityResponse]
    top_keywords: list[str]
    top_categories: list[str]
    top_topics: list[str]
    active_signals_count: int
    knowledge_coverage: float
    model_version: str


class TimelineSnapshotResponse(BaseModel):
    """A single point-in-time snapshot of a metric.

    Attributes:
        value: Metric value at this point in time.
        sample_size: Number of data points backing this metric.
        recorded_at: When this snapshot was recorded.
    """

    value: float
    sample_size: int
    recorded_at: str


class TimelineResponse(BaseModel):
    """Historical evolution of a knowledge metric.

    Attributes:
        entity_type: Type of entity (source, keyword, category, topic).
        entity_id: Entity identifier.
        metric_name: Name of the tracked metric.
        snapshots: Chronologically ordered snapshots.
        trend: Trend direction (IMPROVING, DECLINING, STABLE, INSUFFICIENT_DATA).
    """

    entity_type: str
    entity_id: str
    metric_name: str
    snapshots: list[TimelineSnapshotResponse]
    trend: str


class SignalResponse(BaseModel):
    """An active learning signal.

    Attributes:
        signal_type: Dimension of the signal (KEYWORD, SOURCE, etc.).
        dimension: Specific value within the dimension.
        strength: Signal strength (0.0-1.0).
        decay_factor: Time-based decay factor.
        sample_size: Number of contributing records.
        approval_rate: Approval rate among contributing records.
        window_start: Start of the measurement window.
        window_end: End of the measurement window.
        last_updated: When the signal was last updated.
    """

    signal_type: str
    dimension: str
    strength: float
    decay_factor: float
    sample_size: int
    approval_rate: float
    window_start: str
    window_end: str
    last_updated: str


class DatasetResponse(BaseModel):
    """Versioned dataset metadata.

    Attributes:
        dataset_id: Unique dataset identifier.
        version: Semantic version string.
        created_at: When the dataset was created.
        algorithm_version: Algorithm version used.
        record_count: Number of records in the dataset.
        approved_count: Number of approved records.
        rejected_count: Number of rejected records.
        export_format: Export format (JSONL, CSV).
        checksum: Integrity checksum.
        description: Human-readable description.
        status: Current status (PENDING, ACTIVE, ARCHIVED).
    """

    dataset_id: str
    version: str
    created_at: str
    algorithm_version: str
    record_count: int
    approved_count: int
    rejected_count: int
    export_format: str
    checksum: str
    description: str
    status: str


class ArtifactResponse(BaseModel):
    """Knowledge artifact metadata.

    Attributes:
        artifact_id: Unique artifact identifier.
        artifact_type: Type (DATASET, MODEL, REPORT, SNAPSHOT).
        version: Semantic version string.
        created_at: When the artifact was created.
        created_by: Who created the artifact.
        source_dataset: Source dataset ID.
        algorithm_version: Algorithm version used.
        checksum: Integrity checksum.
        status: Current lifecycle status.
    """

    artifact_id: str
    artifact_type: str
    version: str
    created_at: str
    created_by: str
    source_dataset: str
    algorithm_version: str
    checksum: str
    status: str


class AnalyticsResponse(BaseModel):
    """Comprehensive learning analytics.

    Attributes:
        total_feedback: Total number of feedback records.
        approval_ratio: Ratio of approvals to total decisions.
        total_signals: Total number of active signals.
        signals_by_dimension: Signal count grouped by dimension.
        average_approval_rate: Average approval rate across sources.
        top_sources: Sources with highest approval rates.
        model_version: Current model version.
    """

    total_feedback: int
    approval_ratio: float
    total_signals: int
    signals_by_dimension: dict[str, int]
    average_approval_rate: float
    top_sources: list[SourceQualityResponse]
    model_version: str


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper.

    Attributes:
        items: List of items in this page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        has_next: Whether there are more pages.
    """

    items: list[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
