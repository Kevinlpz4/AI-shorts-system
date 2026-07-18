"""
DatasetMetadataMapper — Domain <-> SQLAlchemy model mapping for Dataset Registry.
"""
from __future__ import annotations

from datetime import datetime

from learning.persistence.models.dataset_metadata import DatasetMetadataModel


class _DatasetMetadata:
    """Lightweight domain representation of dataset metadata."""

    def __init__(
        self,
        dataset_version: str,
        algorithm_version: str,
        feature_schema_version: str,
        record_count: int = 0,
        approved_count: int = 0,
        rejected_count: int = 0,
        export_format: str = "JSON",
        checksum: str = "",
        description: str = "",
        status: str = "PENDING",
        created_at: datetime | None = None,
        id: str | None = None,
    ) -> None:
        self.id = id
        self.dataset_version = dataset_version
        self.created_at = created_at or datetime.now()
        self.algorithm_version = algorithm_version
        self.feature_schema_version = feature_schema_version
        self.record_count = record_count
        self.approved_count = approved_count
        self.rejected_count = rejected_count
        self.export_format = export_format
        self.checksum = checksum
        self.description = description
        self.status = status


class DatasetMetadataMapper:
    """Maps dataset metadata domain <-> DatasetMetadataModel."""

    @staticmethod
    def to_domain(model: DatasetMetadataModel) -> _DatasetMetadata:
        """Convert SQLAlchemy model to domain representation."""
        return _DatasetMetadata(
            id=model.id,
            dataset_version=model.dataset_version,
            created_at=model.created_at,
            algorithm_version=model.algorithm_version,
            feature_schema_version=model.feature_schema_version,
            record_count=model.record_count,
            approved_count=model.approved_count,
            rejected_count=model.rejected_count,
            export_format=model.export_format,
            checksum=model.checksum,
            description=model.description,
            status=model.status,
        )

    @staticmethod
    def to_model(entity: _DatasetMetadata, version: int = 1) -> DatasetMetadataModel:
        """Convert domain representation to SQLAlchemy model."""
        return DatasetMetadataModel(
            id=entity.id or "",
            dataset_version=entity.dataset_version,
            created_at=entity.created_at,
            algorithm_version=entity.algorithm_version,
            feature_schema_version=entity.feature_schema_version,
            record_count=entity.record_count,
            approved_count=entity.approved_count,
            rejected_count=entity.rejected_count,
            export_format=entity.export_format,
            checksum=entity.checksum,
            description=entity.description,
            status=entity.status,
            version=version,
        )
