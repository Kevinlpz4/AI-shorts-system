"""
KnowledgeSnapshotModel — SQLAlchemy model for append-only knowledge snapshots.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class KnowledgeSnapshotModel(Base):
    """Persistence model for KnowledgeSnapshot (append-only, never updated)."""

    __tablename__ = "learning_knowledge_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(255), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False, default=0)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json = Column(Text, nullable=False, default="{}")  # JSON
    # NO version column — append-only, never updated
