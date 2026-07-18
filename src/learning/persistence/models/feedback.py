"""
FeedbackRecordModel — SQLAlchemy model for FeedbackRecord aggregate root.

Immutable: only INSERT, never UPDATE.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from learning.persistence.models.base import Base


class FeedbackRecordModel(Base):
    """Persistence model for FeedbackRecord (immutable)."""

    __tablename__ = "learning_feedback"

    id = Column(String(36), primary_key=True)
    topic_id = Column(String(255), nullable=False, index=True)
    decision = Column(String(50), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    feature_snapshot_json = Column(Text, nullable=False)  # JSON
    source_name = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=False)
    score_snapshot_json = Column(Text, nullable=False)  # JSON
    captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
