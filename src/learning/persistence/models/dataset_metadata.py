"""
DatasetMetadataModel — SQLAlchemy model for Dataset Registry.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from learning.persistence.models.base import Base


class DatasetMetadataModel(Base):
    """Persistence model for dataset metadata (Dataset Registry)."""

    __tablename__ = "learning_datasets"

    id = Column(String(36), primary_key=True)
    dataset_version = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    algorithm_version = Column(String(20), nullable=False)
    feature_schema_version = Column(String(20), nullable=False)
    record_count = Column(Integer, nullable=False, default=0)
    approved_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    export_format = Column(String(20), nullable=False, default="JSON")
    checksum = Column(String(255), nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    version = Column(Integer, nullable=False, default=1)
