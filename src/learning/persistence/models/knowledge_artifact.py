"""
KnowledgeArtifactModel — SQLAlchemy model for KnowledgeArtifact entity.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from learning.persistence.models.base import Base


class KnowledgeArtifactModel(Base):
    """Persistence model for KnowledgeArtifact."""

    __tablename__ = "learning_knowledge_artifacts"

    id = Column(String(36), primary_key=True)
    artifact_type = Column(String(20), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by = Column(String(255), nullable=False)
    source_dataset = Column(String(255), nullable=False, default="")
    algorithm_version = Column(String(20), nullable=False, default="")
    feature_version = Column(String(20), nullable=False, default="")
    checksum = Column(String(255), nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")  # JSON
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    version_int = Column("version_int", Integer, nullable=False, default=1)  # Optimistic locking
