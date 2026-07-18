"""
Consistency Tests — Immutability, versioning, append-only guarantees.

Verifies domain invariants are enforced at the infrastructure level.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.domain.entities.ids import FeedbackId
from learning.domain.entities.knowledge_artifact import (
    KnowledgeArtifact,
    ArtifactType,
    ArtifactStatus,
)
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.ids import LearningModelId
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.exceptions import LearningDomainError

from learning.integration.observability.knowledge_timeline import KnowledgeSnapshot
from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage

from tests.learning.e2e.conftest import record_approve


class TestImmutability:
    """Verify immutable entities cannot be modified after creation."""

    def test_feedback_record_never_changes(self, seeded_factory: LearningServiceFactory):
        """FeedbackRecord is immutable — once created, never modified."""
        result = record_approve(
            seeded_factory,
            topic_id="imm-1",
            source_name="reuters",
            title="Immutable Article",
        )
        assert result.is_success

        fb_id = FeedbackId.from_string(result.value.id)
        record = seeded_factory.feedback_repo.find_by_id(fb_id).value

        # Attempting to modify any field raises AttributeError
        with pytest.raises(AttributeError, match="immutable"):
            record.topic_id = "hacked"

        with pytest.raises(AttributeError, match="immutable"):
            record.source_name = "hacked"

        with pytest.raises(AttributeError, match="immutable"):
            record.title = "hacked"

    def test_knowledge_snapshot_never_changes(self):
        """KnowledgeSnapshot is frozen dataclass — immutable."""
        snapshot = KnowledgeSnapshot(
            entity_type="source",
            entity_id="reuters",
            metric_name="approval_rate",
            metric_value=0.8,
            sample_size=10,
            snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        with pytest.raises(AttributeError):
            snapshot.metric_value = 0.9

        with pytest.raises(AttributeError):
            snapshot.entity_id = "hacked"

    def test_dataset_metadata_never_overwritten(self, seeded_factory: LearningServiceFactory):
        """DatasetDTO is frozen — fields cannot be reassigned."""
        from learning.application.commands.dataset_commands import GenerateDatasetCommand

        record_approve(
            seeded_factory,
            topic_id="ds-imm",
            source_name="src",
            title="Article",
        )

        result = seeded_factory.dataset_service.execute_generate_dataset(
            GenerateDatasetCommand(
                name="Immutable dataset",
                time_window_start="2020-01-01T00:00:00Z",
                time_window_end="2030-12-31T23:59:59Z",
            )
        )
        assert result.is_success
        dto = result.value

        with pytest.raises(AttributeError):
            dto.name = "hacked"

    def test_knowledge_artifact_preserves_checksum(self):
        """KnowledgeArtifact maintains checksum integrity via set_checksum."""
        artifact = KnowledgeArtifact(
            artifact_type=ArtifactType.DATASET,
            version="1.0.0",
        )

        # Initially empty
        assert artifact.checksum == ""

        # Set checksum
        artifact.set_checksum("sha256:abc123")
        assert artifact.checksum == "sha256:abc123"

        # Verify it persists (not overwritten by lifecycle transitions)
        artifact.activate()
        assert artifact.checksum == "sha256:abc123"

    def test_versions_never_overwritten(self):
        """LearningModel.update_version enforces monotonically increasing versions."""
        model = LearningModel(
            id=LearningModelId.generate(),
            algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
            current_weights=ScoreWeights(
                relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
            ),
            minimum_confidence=0.5,
            minimum_sample_size=5,
        )

        # Upgrade works
        model.update_version(AlgorithmVersion(major=1, minor=1, patch=0))
        assert str(model.algorithm_version) == "1.1.0"

        # Downgrade fails
        with pytest.raises(LearningDomainError):
            model.update_version(AlgorithmVersion(major=1, minor=0, patch=0))

        # Same version fails
        with pytest.raises(LearningDomainError):
            model.update_version(AlgorithmVersion(major=1, minor=1, patch=0))

    def test_timeline_is_append_only(self):
        """KnowledgeTimelineStorage never deletes or modifies snapshots."""
        storage = KnowledgeTimelineStorage()

        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="reuters",
                metric_name="approval_rate",
                metric_value=0.7,
                sample_size=10,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )

        assert storage.snapshot_count() == 1

        # There is no delete or update method — only append
        # Verify the snapshot is unchanged
        evolution = storage.get_timeline("source", "reuters", "approval_rate")
        assert len(evolution.snapshots) == 1
        assert evolution.snapshots[0].metric_value == 0.7

    def test_feature_snapshot_is_immutable(self):
        """FeatureSnapshot is frozen dataclass."""
        from learning.domain.value_objects.feature_snapshot import FeatureSnapshot

        snapshot = FeatureSnapshot(
            base_score=0.5,
            freshness_score=0.6,
            keyword_bonus=0.7,
            source_bonus=0.8,
            topic_penalty=0.1,
            confidence=0.9,
            final_score=0.75,
            timestamp=datetime.now(timezone.utc),
        )

        with pytest.raises(AttributeError):
            snapshot.final_score = 0.99

    def test_score_weights_are_immutable(self):
        """ScoreWeights is frozen dataclass."""
        weights = ScoreWeights(
            relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
        )

        with pytest.raises(AttributeError):
            weights.relevance = 0.9
