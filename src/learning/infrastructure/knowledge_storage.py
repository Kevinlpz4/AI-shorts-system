"""
Knowledge Timeline Storage — append-only persistence for KnowledgeSnapshots.

Provides persistent storage for the Knowledge Timeline system.
Snapshots are append-only — the system NEVER recalculates history.

Usage::

    storage = KnowledgeTimelineStorage()
    storage.append(KnowledgeSnapshot(
        entity_type="source",
        entity_id="reuters",
        metric_name="approval_rate",
        metric_value=0.85,
    ))

    evolution = storage.get_timeline("source", "reuters", "approval_rate")
    assert evolution.latest_value() == 0.85
"""
from __future__ import annotations

from collections import defaultdict

from learning.integration.observability.knowledge_timeline import (
    KnowledgeEvolution,
    KnowledgeSnapshot,
)


class KnowledgeTimelineStorage:
    """Persistent storage for KnowledgeSnapshots.

    Append-only. Never recalculates history. Snapshots are stored
    in insertion order and queried by entity type, entity ID, and
    metric name.

    Usage::

        storage = KnowledgeTimelineStorage()
        storage.append(snapshot)
        evolution = storage.get_timeline("source", "reuters", "approval_rate")
    """

    def __init__(self) -> None:
        self._snapshots: list[KnowledgeSnapshot] = []

    def append(self, snapshot: KnowledgeSnapshot) -> None:
        """Append a single snapshot to the timeline."""
        self._snapshots.append(snapshot)

    def append_batch(self, snapshots: list[KnowledgeSnapshot]) -> None:
        """Append multiple snapshots to the timeline."""
        self._snapshots.extend(snapshots)

    def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
    ) -> KnowledgeEvolution:
        """Get the knowledge evolution for a specific entity and metric.

        Returns a KnowledgeEvolution with matching snapshots ordered
        chronologically (oldest first).

        Args:
            entity_type: Type of entity to filter (e.g., "source", "dimension").
            entity_id: ID of the entity to filter.
            metric_name: Name of the metric to filter.

        Returns:
            KnowledgeEvolution with matching snapshots.
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
            snapshots=tuple(sorted(matching, key=lambda s: s.snapshot_at)),
        )

    def get_all_for_entity(
        self, entity_type: str, entity_id: str
    ) -> list[KnowledgeSnapshot]:
        """Get all snapshots for a specific entity, across all metrics.

        Args:
            entity_type: Type of entity to filter.
            entity_id: ID of the entity to filter.

        Returns:
            List of matching snapshots (unsorted).
        """
        return [
            s
            for s in self._snapshots
            if s.entity_type == entity_type and s.entity_id == entity_id
        ]

    def aggregate(self, entity_type: str, metric_name: str) -> dict[str, float]:
        """Aggregate metric values across all entities of a type.

        Computes the average metric value per entity for the given
        entity type and metric name.

        Args:
            entity_type: Type of entity to aggregate.
            metric_name: Name of the metric to aggregate.

        Returns:
            Dict mapping entity_id → average metric value.
        """
        entity_values: dict[str, list[float]] = defaultdict(list)
        for s in self._snapshots:
            if s.entity_type == entity_type and s.metric_name == metric_name:
                entity_values[s.entity_id].append(s.metric_value)
        return {eid: sum(vals) / len(vals) for eid, vals in entity_values.items()}

    def snapshot_count(self) -> int:
        """Total number of stored snapshots."""
        return len(self._snapshots)
