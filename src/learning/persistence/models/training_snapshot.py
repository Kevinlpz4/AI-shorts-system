"""
TrainingSnapshotModel — SQLAlchemy model for training snapshots.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class TrainingSnapshotModel(Base):
    """Persistence model for training snapshots."""

    __tablename__ = "learning_training_snapshots"

    id = Column(String(36), primary_key=True)
    dataset_version = Column(String(20), nullable=False, index=True)
    algorithm_version = Column(String(20), nullable=False)
    feature_version = Column(String(20), nullable=False)
    weights_json = Column(Text, nullable=False)  # JSON
    confidence_threshold = Column(Float, nullable=False, default=0.5)
    training_parameters_json = Column(Text, nullable=False, default="{}")  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    version = Column(Integer, nullable=False, default=1)
