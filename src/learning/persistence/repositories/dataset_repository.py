"""
DatasetRepository — Persistence for dataset metadata (Dataset Registry).

Each save() creates a new version. Versions are never overwritten.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from learning.persistence.mappers.dataset_metadata_mapper import (
    DatasetMetadataMapper,
    _DatasetMetadata,
)
from learning.persistence.models.dataset_metadata import DatasetMetadataModel


class DatasetRepository:
    """Repository for dataset metadata persistence (Dataset Registry)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, dataset: _DatasetMetadata) -> _DatasetMetadata:
        """Persist a new dataset version (never overwrites existing).

        Always creates a new record — versions are immutable.
        """
        # Check if this exact version already exists
        existing = (
            self._session.query(DatasetMetadataModel)
            .filter(
                DatasetMetadataModel.dataset_version == dataset.dataset_version,
            )
            .first()
        )
        if existing is not None:
            raise ValueError(
                f"Dataset version {dataset.dataset_version} already exists "
                f"(versions are immutable — cannot overwrite)"
            )
        model = DatasetMetadataMapper.to_model(dataset)
        self._session.add(model)
        self._session.flush()
        return DatasetMetadataMapper.to_domain(model)

    def find_by_version(self, dataset_version: str) -> _DatasetMetadata | None:
        """Find a dataset by its version string."""
        model = (
            self._session.query(DatasetMetadataModel)
            .filter(DatasetMetadataModel.dataset_version == dataset_version)
            .first()
        )
        if model is None:
            return None
        return DatasetMetadataMapper.to_domain(model)

    def find_all(self) -> list[_DatasetMetadata]:
        """Return all dataset versions ordered by creation time."""
        models = (
            self._session.query(DatasetMetadataModel)
            .order_by(DatasetMetadataModel.created_at.desc())
            .all()
        )
        return [DatasetMetadataMapper.to_domain(m) for m in models]

    def find_by_status(self, status: str) -> list[_DatasetMetadata]:
        """Return all datasets with a specific status."""
        models = (
            self._session.query(DatasetMetadataModel)
            .filter(DatasetMetadataModel.status == status)
            .order_by(DatasetMetadataModel.created_at.desc())
            .all()
        )
        return [DatasetMetadataMapper.to_domain(m) for m in models]

    def count_all(self) -> int:
        """Count all dataset versions."""
        from sqlalchemy import func

        count = self._session.query(func.count(DatasetMetadataModel.id)).scalar()
        return count or 0
