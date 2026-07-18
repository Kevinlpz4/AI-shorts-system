"""
Shared fixtures for Learning Engine E2E tests.

Provides pre-configured factory instances and seeded data
for comprehensive integration testing.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.entities.ids import SourceQualityId


def _ensure_source_profile(factory: LearningServiceFactory, source_name: str) -> None:
    """Create a SourceQualityProfile for source_name if it doesn't exist yet.

    DecisionService only updates existing profiles — it doesn't create them.
    This helper ensures profiles exist before recording feedback.
    """
    existing = factory.source_quality_repo.find_by_source_name(source_name)
    if existing.is_failure:
        profile = SourceQualityProfile(
            id=SourceQualityId.generate(),
            source_name=source_name,
        )
        factory.source_quality_repo.save(profile)


@pytest.fixture
def factory():
    """Fresh LearningServiceFactory with empty in-memory repos."""
    return LearningServiceFactory()


@pytest.fixture
def seeded_factory():
    """Factory with pre-seeded model and source profiles.

    Seeds:
        - LearningModel v1.0.0 with balanced weights
        - SourceQualityProfile for "reuters"
    """
    f = LearningServiceFactory()

    # Seed a LearningModel
    from learning.domain.entities.learning_model import LearningModel
    from learning.domain.entities.ids import LearningModelId
    from learning.domain.value_objects.algorithm_version import AlgorithmVersion
    from learning.domain.value_objects.score_weights import ScoreWeights

    model = LearningModel(
        id=LearningModelId.generate(),
        algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
        current_weights=ScoreWeights(
            relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
        ),
        minimum_confidence=0.3,
        minimum_sample_size=5,
    )
    f.model_repo.save(model)

    # Seed a SourceQualityProfile
    profile = SourceQualityProfile(
        id=SourceQualityId.generate(),
        source_name="reuters",
    )
    f.source_quality_repo.save(profile)

    return f


def record_approve(
    factory: LearningServiceFactory,
    topic_id: str,
    source_name: str,
    title: str,
    features: dict[str, float] | None = None,
):
    """Helper to record an APPROVED feedback.

    Automatically creates a SourceQualityProfile for the source if needed.
    """
    _ensure_source_profile(factory, source_name)
    cmd = RecordFeedbackCommand(
        topic_id=topic_id,
        decision="APPROVED",
        reason=None,
        source_name=source_name,
        title=title,
        features=features,
    )
    return factory.decision_service.execute_record_feedback(cmd)


def record_reject(
    factory: LearningServiceFactory,
    topic_id: str,
    source_name: str,
    title: str,
    reason: str = "Low quality",
    features: dict[str, float] | None = None,
):
    """Helper to record a REJECTED feedback.

    Automatically creates a SourceQualityProfile for the source if needed.
    """
    _ensure_source_profile(factory, source_name)
    cmd = RecordFeedbackCommand(
        topic_id=topic_id,
        decision="REJECTED",
        reason=reason,
        source_name=source_name,
        title=title,
        features=features,
    )
    return factory.decision_service.execute_record_feedback(cmd)
