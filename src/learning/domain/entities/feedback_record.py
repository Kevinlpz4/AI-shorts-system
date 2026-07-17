"""
FeedbackRecord — Aggregate Root Inmutable del BC Learning.

Registra una decisión humana sobre contenido. Es TOTALMENTE inmutable —
una vez creado, nunca se modifica (como RawArticle en Ingestion).

TÉCNICAMENTE hereda de ``AggregateRoot`` por ser el punto de entrada
de consistencia para la grabación de decisiones.

Invariantes:
  - I-01: IMMUTABLE — No modification after creation
  - I-02: topic_id MUST NOT be empty
  - I-03: decision MUST be a valid DecisionType
  - I-04: reason MUST be provided for REJECTED, AUTO_REJECTED, OVERRIDDEN
  - I-05: source_name MUST NOT be empty
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from foundation.base.aggregate_root import AggregateRoot

from learning.domain.entities.ids import FeedbackId
from learning.domain.events.learning_events import FeedbackCaptured
from learning.domain.exceptions import LearningDomainError
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot


class _RejectionDecisions:
    """Decision types that require a reason."""

    REASONS_REQUIRED = frozenset(
        {DecisionType.REJECTED, DecisionType.AUTO_REJECTED, DecisionType.OVERRIDDEN}
    )


@dataclass(eq=False, init=False)
class FeedbackRecord(AggregateRoot):
    """Immutable record of a human/AI decision on content.

    Once created, a FeedbackRecord can NEVER be modified. This ensures
    historical accuracy and auditability of the decision trail.

    Attributes:
        id: Unique identity of this feedback record.
        topic_id: String identifier of the topic (references topic in Ingestion).
        decision: Type of decision made (APPROVED, REJECTED, etc.).
        reason: Reason for rejection/override (required for rejection types).
        feature_snapshot: Snapshot of scoring features at decision time.
        source_name: Name of the source the content came from.
        title: Title of the content that was decided on.
        score_snapshot: Dict of score components at decision time.
        captured_at: When the decision was captured.
    """

    id: FeedbackId
    topic_id: str
    decision: DecisionType
    reason: str | None
    feature_snapshot: FeatureSnapshot
    source_name: str
    title: str
    score_snapshot: dict
    captured_at: datetime

    def __init__(
        self,
        id: FeedbackId,
        topic_id: str,
        decision: DecisionType,
        reason: str | None,
        feature_snapshot: FeatureSnapshot,
        source_name: str,
        title: str,
        score_snapshot: dict | None = None,
        captured_at: datetime | None = None,
    ) -> None:
        """Initialize an immutable FeedbackRecord.

        Args:
            id: Unique identity.
            topic_id: Topic identifier (string).
            decision: Type of decision.
            reason: Reason for rejection/override (required for rejection types).
            feature_snapshot: Snapshot of scoring features.
            source_name: Source name.
            title: Content title.
            score_snapshot: Score components dict (default: empty dict).
            captured_at: Capture timestamp (default: now UTC).

        Raises:
            LearningDomainError: If any invariant is violated.
        """
        from datetime import datetime, timezone

        # I-02: topic_id must not be empty
        if not topic_id or not topic_id.strip():
            raise LearningDomainError(
                "FeedbackRecord.topic_id must not be empty (I-02)"
            )

        # I-03: decision must be valid (already enforced by DecisionType enum)

        # I-04: reason required for rejection types
        if decision in _RejectionDecisions.REASONS_REQUIRED:
            if not reason or not reason.strip():
                raise LearningDomainError(
                    "FeedbackRecord.reason is required for "
                    f"{decision.value} decisions (I-04)"
                )

        # I-05: source_name must not be empty
        if not source_name or not source_name.strip():
            raise LearningDomainError(
                "FeedbackRecord.source_name must not be empty (I-05)"
            )

        # Use object.__setattr__ for all fields
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "topic_id", topic_id.strip())
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "feature_snapshot", feature_snapshot)
        object.__setattr__(self, "source_name", source_name.strip())
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "score_snapshot", score_snapshot or {})
        object.__setattr__(
            self,
            "captured_at",
            captured_at or datetime.now(timezone.utc),
        )
        # Initialize AggregateRoot._events
        object.__setattr__(self, "_events", [])

        # Emit domain event
        self.register_event(
            FeedbackCaptured(
                feedback_id=self.id,
                topic_id=self.topic_id,
                decision=self.decision,
                source_name=self.source_name,
                captured_at=self.captured_at,
            )
        )

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent mutation after construction (I-01)."""
        if hasattr(self, "_events") and name != "_events":
            raise AttributeError(
                f"FeedbackRecord is immutable (I-01): cannot modify '{name}'"
            )
        object.__setattr__(self, name, value)
