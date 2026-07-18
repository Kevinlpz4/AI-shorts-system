"""
LearningModelModel — SQLAlchemy model for LearningModel aggregate root.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class LearningModelModel(Base):
    """Persistence model for LearningModel."""

    __tablename__ = "learning_models"

    id = Column(String(36), primary_key=True)
    algorithm_version_str = Column(String(20), nullable=False)  # "1.2.3"
    weights_json = Column(Text, nullable=False)  # JSON
    minimum_confidence = Column(Float, nullable=False, default=0.5)
    minimum_sample_size = Column(Integer, nullable=False, default=10)
    active_rules_json = Column(Text, nullable=False, default="[]")  # JSON array
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, default=1)
