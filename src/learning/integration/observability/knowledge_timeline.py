"""
Knowledge Timeline — architecture for tracking knowledge evolution over time.

PREPARED but NOT fully connected yet. Future use: answer questions like
"Why does the system prefer Reuters now?" or "When did this source start
being approved more often?"

Building blocks:
    - KnowledgeSnapshot: A point-in-time snapshot of a metric for an entity
    - KnowledgeEvolution: Tracks how a metric evolved over time
    - KnowledgeTimelineCollector: Collects snapshots and builds timelines

Future: listens to ScoreAdjusted, SignalAggregated, LearningModelUpdated
and creates KnowledgeSnapshots for timeline tracking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """A point-in-time snapshot of knowledge about a source/dimension.

    This is the building block for Knowledge Timeline.
    Each snapshot captures the state at a specific moment.

    Attributes:
        entity_type: Type of entity ("source", "dimension", "keyword").
        entity_id: Identifier for the entity (e.g., source name, keyword).
        metric_name: Name of the metric (e.g., "approval_rate", "quality_score").
        metric_value: Value of the metric at snapshot time.
        sample_size: Number of data points backing this metric.
        snapshot_at: When this snapshot was taken.
        metadata: Additional context for the snapshot.
    """

    entity_type: str = ""  # "source", "dimension", "keyword"
    entity_id: str = ""  # e.g., source name, keyword
    metric_name: str = ""  # "approval_rate", "quality_score", "signal_strength"
    metric_value: float = 0.0
    sample_size: int = 0
    snapshot_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEvolution:
    """Tracks how a metric evolved over time for an entity.

    Future use: answer questions like "Why does the system prefer Reuters now?"
    or "When did this source start being approved more often?"

    Attributes:
        entity_type: Type of entity.
        entity_id: Identifier for the entity.
        metric_name: Name of the metric.
        snapshots: Ordered tuple of snapshots (oldest first).
    """

    entity_type: str = ""
    entity_id: str = ""
    metric_name: str = ""
    snapshots: tuple[KnowledgeSnapshot, ...] = ()

    def latest_value(self) -> float:
        """Get the most recent metric value."""
        return self.snapshots[-1].metric_value if self.snapshots else 0.0

    def trend(self) -> str:
        """Calculate trend: IMPROVING, DECLINING, STABLE, INSUFFICIENT_DATA.

        Uses first and last snapshot values with a 5% threshold.
        """
        if len(self.snapshots) < 2:
            return "INSUFFICIENT_DATA"
        values = [s.metric_value for s in self.snapshots]
        if values[-1] > values[0] * 1.05:
            return "IMPROVING"
        elif values[-1] < values[0] * 0.95:
            return "DECLINING"
        return "STABLE"

    def period(self) -> tuple[datetime, datetime] | None:
        """Get the time period covered by snapshots."""
        if not self.snapshots:
            return None
        return (self.snapshots[0].snapshot_at, self.snapshots[-1].snapshot_at)


class KnowledgeTimelineCollector:
    """Collects KnowledgeSnapshots from Learning events.

    NOT implemented yet — architecture prepared only.
    Future: listens to ScoreAdjusted, SignalAggregated, LearningModelUpdated
    and creates KnowledgeSnapshots for timeline tracking.
    """

    def __init__(self) -> None:
        self._snapshots: list[KnowledgeSnapshot] = []

    def collect(self, snapshot: KnowledgeSnapshot) -> None:
        """Collect a knowledge snapshot."""
        self._snapshots.append(snapshot)

    def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
    ) -> KnowledgeEvolution:
        """Get the knowledge evolution for a specific entity and metric.

        Args:
            entity_type: Type of entity to filter.
            entity_id: ID of the entity to filter.
            metric_name: Name of the metric to filter.

        Returns:
            KnowledgeEvolution with matching snapshots ordered chronologically.
        """
        matching = [
            s
            for s in self._snapshots
            if s.entity_type == entity_type
            and s.entity_id == entity_id
            and s.metric_name == metric_name
        ]
        return KnowledgeEvolution(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            snapshots=tuple(matching),
        )

    def snapshot_count(self) -> int:
        """Return total number of collected snapshots."""
        return len(self._snapshots)
