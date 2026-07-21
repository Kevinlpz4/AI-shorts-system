"""
SQLAlchemy ORM models for Runtime persistence.

Models are NOT domain entities. They are data-mapper representations
for operational data: validation metrics, dataset versions, and
runtime configuration.

Design principles:
    1. Models are lightweight — no complex relationships.
    2. Tables use the ``runtime_`` prefix to avoid collisions with BC tables.
    3. JSON columns for flexible metadata storage.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class _RuntimeBase(DeclarativeBase):
    """Base class for Runtime ORM models.

    Separate from BC bases to avoid metadata collisions.
    """
    pass


class ValidationMetricsModel(_RuntimeBase):
    """ORM model for ``runtime_validation_metrics`` table.

    Stores validation accuracy metrics tracked over time windows.
    """

    __tablename__ = "runtime_validation_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    window_days = Column(Integer, nullable=False)
    algorithm_version = Column(String(50), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, default=dict)


class DatasetVersionModel(_RuntimeBase):
    """ORM model for ``runtime_dataset_versions`` table.

    Tracks dataset snapshots with checksums for reproducibility.
    """

    __tablename__ = "runtime_dataset_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True)
    snapshot_date = Column(DateTime, nullable=False)
    total_samples = Column(Integer, default=0)
    labeled_samples = Column(Integer, default=0)
    checksum = Column(String(64), nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class RuntimeConfigurationModel(_RuntimeBase):
    """ORM model for ``runtime_configuration`` table.

    Key-value store for runtime configuration overrides.
    """

    __tablename__ = "runtime_configuration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(200), nullable=False, unique=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
    )
