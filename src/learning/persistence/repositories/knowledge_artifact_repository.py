"""
KnowledgeArtifactRepository — CRUD persistence for KnowledgeArtifact.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from learning.domain.entities.knowledge_artifact import (
    ArtifactStatus,
    ArtifactType,
    KnowledgeArtifact,
)
from learning.domain.entities.ids import KnowledgeArtifactId
from learning.persistence.mappers.knowledge_artifact_mapper import KnowledgeArtifactMapper
from learning.persistence.models.knowledge_artifact import KnowledgeArtifactModel


class KnowledgeArtifactRepository:
    """Repository for KnowledgeArtifact CRUD operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, artifact: KnowledgeArtifact, version_int: int = 1) -> KnowledgeArtifact:
        """Persist a KnowledgeArtifact (upsert by id)."""
        existing = (
            self._session.query(KnowledgeArtifactModel)
            .filter(KnowledgeArtifactModel.id == str(artifact.id))
            .first()
        )
        if existing is not None:
            model = KnowledgeArtifactMapper.to_model(artifact, version_int=existing.version_int + 1)
            existing.artifact_type = model.artifact_type
            existing.version = model.version
            existing.created_by = model.created_by
            existing.source_dataset = model.source_dataset
            existing.algorithm_version = model.algorithm_version
            existing.feature_version = model.feature_version
            existing.checksum = model.checksum
            existing.metadata_json = model.metadata_json
            existing.status = model.status
            existing.version_int = model.version_int
        else:
            model = KnowledgeArtifactMapper.to_model(artifact, version_int=version_int)
            self._session.add(model)
        self._session.flush()
        return artifact

    def find_by_id(self, artifact_id: KnowledgeArtifactId) -> KnowledgeArtifact | None:
        """Find a KnowledgeArtifact by its identity."""
        model = (
            self._session.query(KnowledgeArtifactModel)
            .filter(KnowledgeArtifactModel.id == str(artifact_id))
            .first()
        )
        if model is None:
            return None
        return KnowledgeArtifactMapper.to_domain(model)

    def find_by_type(self, artifact_type: ArtifactType) -> list[KnowledgeArtifact]:
        """Find all artifacts of a specific type."""
        models = (
            self._session.query(KnowledgeArtifactModel)
            .filter(KnowledgeArtifactModel.artifact_type == artifact_type.value)
            .order_by(KnowledgeArtifactModel.created_at.desc())
            .all()
        )
        return [KnowledgeArtifactMapper.to_domain(m) for m in models]

    def find_by_status(self, status: ArtifactStatus) -> list[KnowledgeArtifact]:
        """Find all artifacts with a specific status."""
        models = (
            self._session.query(KnowledgeArtifactModel)
            .filter(KnowledgeArtifactModel.status == status.value)
            .order_by(KnowledgeArtifactModel.created_at.desc())
            .all()
        )
        return [KnowledgeArtifactMapper.to_domain(m) for m in models]

    def find_all(self) -> list[KnowledgeArtifact]:
        """Find all artifacts."""
        models = (
            self._session.query(KnowledgeArtifactModel)
            .order_by(KnowledgeArtifactModel.created_at.desc())
            .all()
        )
        return [KnowledgeArtifactMapper.to_domain(m) for m in models]

    def count_all(self) -> int:
        """Count all artifacts."""
        from sqlalchemy import func

        count = self._session.query(func.count(KnowledgeArtifactModel.id)).scalar()
        return count or 0
