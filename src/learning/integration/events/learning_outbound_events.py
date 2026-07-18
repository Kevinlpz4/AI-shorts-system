"""
Learning Outbound Events — integration events FROM Learning BC.

Other BCs can subscribe to these events to react to Learning decisions
and data changes. Each event carries serializable data only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from foundation.events.integration_event import IntegrationEvent


@dataclass(frozen=True)
class RecommendationGenerated(IntegrationEvent):
    """Learning generated a recommendation for new content.

    Signals that Learning has produced a recommendation (APPROVE, REJECT,
    or MANUAL_REVIEW) for an article. Other BCs can use this to trigger
    downstream processing.
    """

    source_boundary: str = "learning"
    recommendation: str = ""  # APPROVE, REJECT, MANUAL_REVIEW
    probability: float = 0.0
    confidence: float = 0.0
    source_name: str = ""
    reasoning: str = ""  # JSON-encoded list of reasons


@dataclass(frozen=True)
class FeedbackRecorded(IntegrationEvent):
    """Learning recorded a feedback decision.

    Signals that a human feedback decision (approve/reject) was recorded
    for a topic. Other BCs can use this for audit trails or analytics.
    """

    source_boundary: str = "learning"
    feedback_id: str = ""
    topic_id: str = ""
    decision: str = ""
    source_name: str = ""


@dataclass(frozen=True)
class LearningSignalUpdated(IntegrationEvent):
    """Learning updated a signal.

    Signals that a learning signal was created or updated. Other BCs
    can use this for monitoring learning progress.
    """

    source_boundary: str = "learning"
    signal_id: str = ""
    signal_type: str = ""
    dimension: str = ""
    strength_value: float = 0.0


@dataclass(frozen=True)
class DatasetReady(IntegrationEvent):
    """Learning generated a dataset.

    Signals that a training dataset has been generated and is ready
    for consumption. Other BCs can use this to trigger ML training
    or data export workflows.
    """

    source_boundary: str = "learning"
    dataset_id: str = ""
    record_count: int = 0
    format: str = ""
