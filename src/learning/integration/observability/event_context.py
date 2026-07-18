"""
Event Context — observability context for event traceability.

Every event in the pipeline carries this context for full traceability
across Bounded Contexts. Supports correlation and causation chains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EventContext:
    """Observability context for event traceability.

    Every event in the pipeline carries this context for full traceability.
    Supports two chains:

    - correlation_id: Groups all events from the same original trigger
    - causation_id: Links an event to the specific event that caused it

    Immutable — use with_causation() and new_correlated() to create
    derived contexts.

    Usage:
        ctx = EventContext(source_bc="ingestion", event_type="RawArticleCollected")
        child = ctx.new_correlated("RecommendationGenerated", aggregate_id="art-123")
    """

    event_id: UUID = field(default_factory=uuid4)
    correlation_id: str = ""
    causation_id: UUID | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: str = ""
    source_bc: str = ""
    event_type: str = ""

    def with_causation(self, causation_id: UUID) -> EventContext:
        """Create a new context with causation_id set (immutable).

        Args:
            causation_id: The event_id of the event that caused this one.

        Returns:
            A new EventContext with the causation_id set.
        """
        return EventContext(
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            occurred_at=self.occurred_at,
            aggregate_id=self.aggregate_id,
            source_bc=self.source_bc,
            event_type=self.event_type,
        )

    def new_correlated(self, event_type: str, aggregate_id: str = "") -> EventContext:
        """Create a new context correlated to this one (same correlation_id).

        The new context gets its own event_id, and its causation_id
        is set to this context's event_id — forming a chain.

        Args:
            event_type: The type of the new event.
            aggregate_id: Optional aggregate ID for the new event.

        Returns:
            A new EventContext linked to this one.
        """
        return EventContext(
            correlation_id=self.correlation_id or str(self.event_id),
            causation_id=self.event_id,
            aggregate_id=aggregate_id,
            source_bc="learning",
            event_type=event_type,
        )
