"""
LearningSignalModel — SQLAlchemy model for LearningSignal aggregate root.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class LearningSignalModel(Base):
    """Persistence model for LearningSignal."""

    __tablename__ = "learning_signals"

    id = Column(String(36), primary_key=True)
    signal_type = Column(String(50), nullable=False, index=True)
    dimension = Column(String(255), nullable=False, index=True)
    strength_json = Column(Text, nullable=False)  # JSON
    sample_size = Column(Integer, nullable=False, default=0)
    approval_rate = Column(Float, nullable=False, default=0.0)
    window_json = Column(Text, nullable=False)  # JSON
    last_updated = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, default=1)
