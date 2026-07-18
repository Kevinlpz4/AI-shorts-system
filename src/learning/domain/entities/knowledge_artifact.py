"""
KnowledgeArtifact — Unified entity for all learning artifacts.

Tracks every artifact produced by the Learning BC: datasets, models,
reports, and snapshots. Enables full reproducibility and auditability.

Every artifact has:
  - A unique identity (KnowledgeArtifactId)
  - A type (DATASET, MODEL, REPORT, SNAPSHOT)
  - A version string
  - Source provenance (which dataset, which algorithm)
  - Integrity verification (checksum)
  - Status tracking (PENDING, ACTIVE, ARCHIVED, DEPRECATED)

KnowledgeArtifact is NOT an Aggregate Root — it's an entity owned
by the Learning BC's knowledge management concern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from foundation.base.entity import Entity

from learning.domain.entities.ids import KnowledgeArtifactId


class ArtifactType(Enum):
    """Types of knowledge artifacts."""
    DATASET = "DATASET"
    MODEL = "MODEL"
    REPORT = "REPORT"
    SNAPSHOT = "SNAPSHOT"


class ArtifactStatus(Enum):
    """Lifecycle status of a knowledge artifact."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"


@dataclass(eq=False)
class KnowledgeArtifact(Entity):
    """Unified knowledge artifact tracking entity.

    Records every artifact produced by the Learning BC with full
    provenance, versioning, and integrity verification.

    Attributes:
        id: Unique artifact identity.
        artifact_type: Type of artifact (DATASET, MODEL, REPORT, SNAPSHOT).
        version: Semantic version string (e.g., "1.0.0").
        created_at: When the artifact was created.
        created_by: Who/what created the artifact (e.g., "dataset_service", "training_pipeline").
        source_dataset: ID of the source dataset (if applicable).
        algorithm_version: Algorithm version used to create this artifact.
        feature_version: Feature schema version used.
        checksum: Integrity checksum (e.g., SHA-256 of content).
        metadata: Arbitrary metadata (JSON-serializable).
        status: Current lifecycle status.

    Invariants:
        - version must be non-empty
        - artifact_type must be a valid ArtifactType
        - status starts as PENDING
        - checksum is set on creation or finalization
    """

    id: KnowledgeArtifactId = field(default_factory=KnowledgeArtifactId.generate)
    artifact_type: ArtifactType = ArtifactType.REPORT
    version: str = "0.0.1"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    source_dataset: str = ""
    algorithm_version: str = ""
    feature_version: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    status: ArtifactStatus = ArtifactStatus.PENDING

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("KnowledgeArtifact.version must be non-empty")

    def activate(self) -> None:
        """Transition to ACTIVE status."""
        if self.status != ArtifactStatus.PENDING:
            raise ValueError(f"Cannot activate artifact in {self.status.value} status")
        self.status = ArtifactStatus.ACTIVE

    def archive(self) -> None:
        """Transition to ARCHIVED status."""
        if self.status not in (ArtifactStatus.ACTIVE, ArtifactStatus.PENDING):
            raise ValueError(f"Cannot archive artifact in {self.status.value} status")
        self.status = ArtifactStatus.ARCHIVED

    def deprecate(self) -> None:
        """Transition to DEPRECATED status."""
        if self.status == ArtifactStatus.ARCHIVED:
            raise ValueError("Cannot deprecate an archived artifact")
        self.status = ArtifactStatus.DEPRECATED

    def set_checksum(self, checksum: str) -> None:
        """Set the integrity checksum."""
        self.checksum = checksum

    def update_metadata(self, key: str, value: Any) -> None:
        """Add or update a metadata field."""
        self.metadata[key] = value

    @property
    def is_active(self) -> bool:
        return self.status == ArtifactStatus.ACTIVE

    @property
    def artifact_type_name(self) -> str:
        return self.artifact_type.value
