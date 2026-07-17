"""
Domain Events for the Learning Bounded Context.

All events inherit from ``DomainEvent`` (Foundation) and are ``@dataclass(frozen=True)``.

Events:
  - FeedbackCaptured: Emitted by FeedbackRecord when a human decision is recorded.
  - SignalAggregated: Emitted by LearningSignal when signal is updated.
  - ScoreAdjusted: Emitted by LearningModel when weights are adjusted.
  - DatasetGenerated: Emitted when a training dataset is generated.
  - LearningModelUpdated: Emitted by LearningModel when algorithm version changes.

NOTE: Child fields use a sentinel default (MISSING) to work around Python's
dataclass field ordering requirement (fields with defaults must come after
fields without defaults in inheritance). The sentinel is validated in
``__post_init__``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from foundation.events.domain_event import DomainEvent

from learning.domain.entities.ids import FeedbackId, LearningModelId, LearningSignalId
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.time_window import TimeWindow


class _MISSING_TYPE:
    """Sentinel type for required dataclass fields with defaults."""

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Any = _MISSING_TYPE()


@dataclass(frozen=True)
class FeedbackCaptured(DomainEvent):
    """Indicates a human decision has been recorded in the Learning BC.

    Emitted by FeedbackRecord when a new decision is captured.

    Attributes:
        feedback_id: FeedbackRecord that was created.
        topic_id: Topic the decision relates to (string ID).
        decision: Type of decision made.
        source_name: Source name the content came from.
        captured_at: When the decision was captured.
    """

    feedback_id: FeedbackId = field(default=MISSING)  # type: ignore[assignment]
    topic_id: str = field(default=MISSING)  # type: ignore[assignment]
    decision: DecisionType = field(default=MISSING)  # type: ignore[assignment]
    source_name: str = field(default=MISSING)  # type: ignore[assignment]
    captured_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        if isinstance(self.feedback_id, _MISSING_TYPE):
            raise TypeError("FeedbackCaptured.feedback_id is required")
        if isinstance(self.topic_id, _MISSING_TYPE):
            raise TypeError("FeedbackCaptured.topic_id is required")
        if isinstance(self.decision, _MISSING_TYPE):
            raise TypeError("FeedbackCaptured.decision is required")
        if isinstance(self.source_name, _MISSING_TYPE):
            raise TypeError("FeedbackCaptured.source_name is required")
        if isinstance(self.captured_at, _MISSING_TYPE):
            raise TypeError("FeedbackCaptured.captured_at is required")


@dataclass(frozen=True)
class SignalAggregated(DomainEvent):
    """Indicates a learning signal has been aggregated or updated.

    Emitted by LearningSignal when signal data is computed from feedback.

    Attributes:
        signal_id: LearningSignal that was updated.
        signal_type: Type of signal.
        dimension: The specific dimension (keyword, source name, etc.).
        strength_value: The computed signal strength value.
        window: Time window of the aggregation.
    """

    signal_id: LearningSignalId = field(default=MISSING)  # type: ignore[assignment]
    signal_type: str = field(default=MISSING)  # type: ignore[assignment]
    dimension: str = field(default=MISSING)  # type: ignore[assignment]
    strength_value: float = field(default=MISSING)
    window: TimeWindow = field(default=MISSING)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if isinstance(self.signal_id, _MISSING_TYPE):
            raise TypeError("SignalAggregated.signal_id is required")
        if isinstance(self.signal_type, _MISSING_TYPE):
            raise TypeError("SignalAggregated.signal_type is required")
        if isinstance(self.dimension, _MISSING_TYPE):
            raise TypeError("SignalAggregated.dimension is required")
        if isinstance(self.strength_value, _MISSING_TYPE):
            raise TypeError("SignalAggregated.strength_value is required")
        if isinstance(self.window, _MISSING_TYPE):
            raise TypeError("SignalAggregated.window is required")


@dataclass(frozen=True)
class ScoreAdjusted(DomainEvent):
    """Indicates scoring weights have been adjusted.

    Emitted by LearningModel when weights are updated based on feedback.

    Attributes:
        model_id: LearningModel whose weights were adjusted.
        old_weights: Previous weight configuration.
        new_weights: New weight configuration.
        reason: Human-readable reason for the adjustment.
        adjusted_at: When the adjustment was made.
    """

    model_id: LearningModelId = field(default=MISSING)  # type: ignore[assignment]
    old_weights: ScoreWeights = field(default=MISSING)  # type: ignore[assignment]
    new_weights: ScoreWeights = field(default=MISSING)  # type: ignore[assignment]
    reason: str = field(default=MISSING)  # type: ignore[assignment]
    adjusted_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        if isinstance(self.model_id, _MISSING_TYPE):
            raise TypeError("ScoreAdjusted.model_id is required")
        if isinstance(self.old_weights, _MISSING_TYPE):
            raise TypeError("ScoreAdjusted.old_weights is required")
        if isinstance(self.new_weights, _MISSING_TYPE):
            raise TypeError("ScoreAdjusted.new_weights is required")
        if isinstance(self.reason, _MISSING_TYPE):
            raise TypeError("ScoreAdjusted.reason is required")
        if isinstance(self.adjusted_at, _MISSING_TYPE):
            raise TypeError("ScoreAdjusted.adjusted_at is required")


@dataclass(frozen=True)
class DatasetGenerated(DomainEvent):
    """Indicates a training dataset has been generated.

    Emitted by the dataset generation service.

    Attributes:
        dataset_id: Unique identifier for the generated dataset.
        version: Version string of the dataset.
        record_count: Number of records in the dataset.
        format: Format of the exported dataset (e.g., 'csv', 'json').
        generated_at: When the dataset was generated.
    """

    dataset_id: str = field(default=MISSING)  # type: ignore[assignment]
    version: str = field(default=MISSING)  # type: ignore[assignment]
    record_count: int = field(default=MISSING)
    format: str = field(default=MISSING)  # type: ignore[assignment]
    generated_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        if isinstance(self.dataset_id, _MISSING_TYPE):
            raise TypeError("DatasetGenerated.dataset_id is required")
        if isinstance(self.version, _MISSING_TYPE):
            raise TypeError("DatasetGenerated.version is required")
        if isinstance(self.record_count, _MISSING_TYPE):
            raise TypeError("DatasetGenerated.record_count is required")
        if isinstance(self.format, _MISSING_TYPE):
            raise TypeError("DatasetGenerated.format is required")
        if isinstance(self.generated_at, _MISSING_TYPE):
            raise TypeError("DatasetGenerated.generated_at is required")
        if self.record_count < 0:
            raise ValueError("DatasetGenerated.record_count must be >= 0")


@dataclass(frozen=True)
class LearningModelUpdated(DomainEvent):
    """Indicates the learning model has been updated to a new version.

    Emitted by LearningModel when algorithm version or active rules change.

    Attributes:
        model_id: LearningModel that was updated.
        old_version: Previous version string.
        new_version: New version string.
        updated_at: When the update was made.
    """

    model_id: LearningModelId = field(default=MISSING)  # type: ignore[assignment]
    old_version: str = field(default=MISSING)  # type: ignore[assignment]
    new_version: str = field(default=MISSING)  # type: ignore[assignment]
    updated_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        if isinstance(self.model_id, _MISSING_TYPE):
            raise TypeError("LearningModelUpdated.model_id is required")
        if isinstance(self.old_version, _MISSING_TYPE):
            raise TypeError("LearningModelUpdated.old_version is required")
        if isinstance(self.new_version, _MISSING_TYPE):
            raise TypeError("LearningModelUpdated.new_version is required")
        if isinstance(self.updated_at, _MISSING_TYPE):
            raise TypeError("LearningModelUpdated.updated_at is required")
