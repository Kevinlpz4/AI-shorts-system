"""
KnowledgeArtifactMapper — Domain <-> SQLAlchemy model mapping for KnowledgeArtifact.
"""
from __future__ import annotations

import json

from learning.domain.entities.knowledge_artifact import (
    ArtifactStatus,
    ArtifactType,
    KnowledgeArtifact,
)
from learning.domain.entities.ids import KnowledgeArtifactId
from learning.persistence.models.knowledge_artifact import KnowledgeArtifactModel


class KnowledgeArtifactMapper:
    """Maps KnowledgeArtifact domain entity <-> KnowledgeArtifactModel."""

    @staticmethod
    def to_domain(model: KnowledgeArtifactModel) -> KnowledgeArtifact:
        """Convert SQLAlchemy model to domain entity."""
        metadata = json.loads(model.metadata_json)
        return KnowledgeArtifact(
            id=KnowledgeArtifactId.from_string(model.id),
            artifact_type=ArtifactType(model.artifact_type),
            version=model.version,
            created_at=model.created_at,
            created_by=model.created_by,
            source_dataset=model.source_dataset,
            algorithm_version=model.algorithm_version,
            feature_version=model.feature_version,
            checksum=model.checksum,
            metadata=metadata,
            status=ArtifactStatus(model.status),
        )

    @staticmethod
    def to_model(entity: KnowledgeArtifact, version_int: int = 1) -> KnowledgeArtifactModel:
        """Convert domain entity to SQLAlchemy model."""
        return KnowledgeArtifactModel(
            id=str(entity.id),
            artifact_type=entity.artifact_type.value,
            version=entity.version,
            created_at=entity.created_at,
            created_by=entity.created_by,
            source_dataset=entity.source_dataset,
            algorithm_version=entity.algorithm_version,
            feature_version=entity.feature_version,
            checksum=entity.checksum,
            metadata_json=json.dumps(entity.metadata),
            status=entity.status.value,
            version_int=version_int,
        )
