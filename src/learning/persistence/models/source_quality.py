"""
SourceQualityProfileModel — SQLAlchemy model for SourceQualityProfile aggregate root.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class SourceQualityProfileModel(Base):
    """Persistence model for SourceQualityProfile."""

    __tablename__ = "learning_source_quality"

    id = Column(String(36), primary_key=True)
    source_name = Column(String(255), nullable=False, unique=True, index=True)
    total_decisions = Column(Integer, nullable=False, default=0)
    approved_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    auto_approved_count = Column(Integer, nullable=False, default=0)
    auto_rejected_count = Column(Integer, nullable=False, default=0)
    overridden_count = Column(Integer, nullable=False, default=0)
    approval_rate = Column(Float, nullable=False, default=0.0)
    keywords_json = Column(Text, nullable=False, default="{}")  # JSON
    last_updated = Column(DateTime(timezone=True), nullable=False)
    version = Column(Integer, nullable=False, default=1)
