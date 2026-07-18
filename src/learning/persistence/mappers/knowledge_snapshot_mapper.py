"""
KnowledgeSnapshotMapper — Domain <-> SQLAlchemy model mapping for KnowledgeSnapshot.

KnowledgeSnapshot is APPEND-ONLY. No update mapping needed.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.persistence.models.knowledge_snapshot import KnowledgeSnapshotModel


class _KnowledgeSnapshot:
    """Lightweight domain representation of a knowledge snapshot.

    Used for round-tripping through the mapper without a full domain entity.
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: float,
        sample_size: int,
        snapshot_at: datetime,
        metadata: dict | None = None,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.sample_size = sample_size
        self.snapshot_at = snapshot_at
        self.metadata = metadata or {}


class KnowledgeSnapshotMapper:
    """Maps KnowledgeSnapshot domain <-> KnowledgeSnapshotModel."""

    @staticmethod
    def to_domain(model: KnowledgeSnapshotModel) -> _KnowledgeSnapshot:
        """Convert SQLAlchemy model to domain representation."""
        metadata = json.loads(model.metadata_json)
        return _KnowledgeSnapshot(
            id=model.id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            metric_name=model.metric_name,
            metric_value=model.metric_value,
            sample_size=model.sample_size,
            snapshot_at=model.snapshot_at,
            metadata=metadata,
        )

    @staticmethod
    def to_model(
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: float,
        sample_size: int,
        snapshot_at: datetime,
        metadata: dict | None = None,
    ) -> KnowledgeSnapshotModel:
        """Create model from snapshot data (append-only, no id)."""
        return KnowledgeSnapshotModel(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            metric_value=metric_value,
            sample_size=sample_size,
            snapshot_at=snapshot_at,
            metadata_json=json.dumps(metadata or {}),
        )
