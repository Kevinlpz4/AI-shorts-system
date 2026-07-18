"""
TrainingSnapshotMapper — Domain <-> SQLAlchemy model mapping for Training Snapshots.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.persistence.models.training_snapshot import TrainingSnapshotModel


class _TrainingSnapshot:
    """Lightweight domain representation of a training snapshot."""

    def __init__(
        self,
        dataset_version: str,
        algorithm_version: str,
        feature_version: str,
        weights: dict[str, float] | None = None,
        confidence_threshold: float = 0.5,
        training_parameters: dict | None = None,
        status: str = "PENDING",
        created_at: datetime | None = None,
        id: str | None = None,
    ) -> None:
        self.id = id
        self.dataset_version = dataset_version
        self.algorithm_version = algorithm_version
        self.feature_version = feature_version
        self.weights = weights or {}
        self.confidence_threshold = confidence_threshold
        self.training_parameters = training_parameters or {}
        self.status = status
        self.created_at = created_at or datetime.now()


class TrainingSnapshotMapper:
    """Maps training snapshot domain <-> TrainingSnapshotModel."""

    @staticmethod
    def to_domain(model: TrainingSnapshotModel) -> _TrainingSnapshot:
        """Convert SQLAlchemy model to domain representation."""
        weights = json.loads(model.weights_json)
        training_parameters = json.loads(model.training_parameters_json)
        return _TrainingSnapshot(
            id=model.id,
            dataset_version=model.dataset_version,
            algorithm_version=model.algorithm_version,
            feature_version=model.feature_version,
            weights=weights,
            confidence_threshold=model.confidence_threshold,
            training_parameters=training_parameters,
            status=model.status,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: _TrainingSnapshot, version: int = 1
    ) -> TrainingSnapshotModel:
        """Convert domain representation to SQLAlchemy model."""
        return TrainingSnapshotModel(
            id=entity.id or "",
            dataset_version=entity.dataset_version,
            algorithm_version=entity.algorithm_version,
            feature_version=entity.feature_version,
            weights_json=json.dumps(entity.weights),
            confidence_threshold=entity.confidence_threshold,
            training_parameters_json=json.dumps(entity.training_parameters),
            created_at=entity.created_at,
            status=entity.status,
            version=version,
        )
