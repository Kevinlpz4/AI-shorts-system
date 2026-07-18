"""
KnowledgeTimelineRepository — Append-only persistence for knowledge snapshots.

Knowledge snapshots are NEVER updated or deleted. New snapshots are
appended to the timeline. This guarantees historical auditability.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from learning.persistence.mappers.knowledge_snapshot_mapper import (
    KnowledgeSnapshotMapper,
)
from learning.persistence.models.knowledge_snapshot import KnowledgeSnapshotModel


class _KnowledgeSnapshot:
    """Lightweight domain representation of a knowledge snapshot."""

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


class KnowledgeTimelineRepository:
    """Append-only repository for knowledge snapshots.

    Guarantees:
      - append() only inserts, never updates
      - get_timeline() returns snapshots ordered by snapshot_at ASC
      - No update or delete methods exist
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: float,
        sample_size: int,
        snapshot_at: datetime,
        metadata: dict | None = None,
    ) -> _KnowledgeSnapshot:
        """Append a new knowledge snapshot (INSERT only).

        Returns the created snapshot with its auto-generated ID.
        """
        model = KnowledgeSnapshotMapper.to_model(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            metric_value=metric_value,
            sample_size=sample_size,
            snapshot_at=snapshot_at,
            metadata=metadata,
        )
        self._session.add(model)
        self._session.flush()
        return KnowledgeSnapshotMapper.to_domain(model)

    def get_timeline(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
    ) -> list[_KnowledgeSnapshot]:
        """Get the full timeline for a specific entity metric.

        Returns snapshots ordered by snapshot_at ASC (oldest first).
        """
        models = (
            self._session.query(KnowledgeSnapshotModel)
            .filter(
                KnowledgeSnapshotModel.entity_type == entity_type,
                KnowledgeSnapshotModel.entity_id == entity_id,
                KnowledgeSnapshotModel.metric_name == metric_name,
            )
            .order_by(KnowledgeSnapshotModel.snapshot_at.asc())
            .all()
        )
        return [KnowledgeSnapshotMapper.to_domain(m) for m in models]

    def get_all_for_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> list[_KnowledgeSnapshot]:
        """Get all snapshots for a specific entity (any metric)."""
        models = (
            self._session.query(KnowledgeSnapshotModel)
            .filter(
                KnowledgeSnapshotModel.entity_type == entity_type,
                KnowledgeSnapshotModel.entity_id == entity_id,
            )
            .order_by(KnowledgeSnapshotModel.snapshot_at.asc())
            .all()
        )
        return [KnowledgeSnapshotMapper.to_domain(m) for m in models]

    def count_for_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> int:
        """Count all snapshots for a specific entity."""
        count = (
            self._session.query(func.count(KnowledgeSnapshotModel.id))
            .filter(
                KnowledgeSnapshotModel.entity_type == entity_type,
                KnowledgeSnapshotModel.entity_id == entity_id,
            )
            .scalar()
        )
        return count or 0

    def get_latest(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
    ) -> _KnowledgeSnapshot | None:
        """Get the most recent snapshot for a specific entity metric."""
        model = (
            self._session.query(KnowledgeSnapshotModel)
            .filter(
                KnowledgeSnapshotModel.entity_type == entity_type,
                KnowledgeSnapshotModel.entity_id == entity_id,
                KnowledgeSnapshotModel.metric_name == metric_name,
            )
            .order_by(KnowledgeSnapshotModel.snapshot_at.desc())
            .first()
        )
        if model is None:
            return None
        return KnowledgeSnapshotMapper.to_domain(model)
