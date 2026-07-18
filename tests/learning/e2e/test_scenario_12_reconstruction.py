"""
Scenario 12: Knowledge Reconstruction (Auditability)

Validates that all components are reconstructible from persisted data.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.queries.prediction_queries import PredictApprovalQuery

from tests.learning.e2e.conftest import record_approve


class TestKnowledgeReconstruction:
    """Verify all components are reconstructible from persisted data."""

    def test_reconstruct_prediction(self, seeded_factory: LearningServiceFactory):
        """Prediction is reconstructible after feedback."""
        source = "audit-source"

        record_approve(
            seeded_factory,
            topic_id="audit-topic",
            source_name=source,
            title="Audit Article",
            features={"final_score": 0.8},
        )

        pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(
                source_name=source, features={"final_score": 0.8}
            )
        )
        assert pred.is_success
        assert 0.0 <= pred.value.probability <= 1.0

    def test_reconstruct_explanation(self, seeded_factory: LearningServiceFactory):
        """Explanation is reconstructible after feedback."""
        source = "audit-source"

        record_approve(
            seeded_factory,
            topic_id="audit-topic-2",
            source_name=source,
            title="Audit Article 2",
            features={"final_score": 0.8},
        )

        expl = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        assert expl.is_success
        assert expl.value.source_name == source

    def test_reconstruct_recommendation(
        self, seeded_factory: LearningServiceFactory
    ):
        """Recommendation is reconstructible after feedback."""
        source = "audit-source"

        record_approve(
            seeded_factory,
            topic_id="audit-topic-3",
            source_name=source,
            title="Audit Article 3",
            features={"final_score": 0.8},
        )

        rec = seeded_factory.recommendation_service.recommend(
            source_name=source
        )
        assert rec.is_success
        assert rec.value.recommendation in ("APPROVE", "REJECT", "MANUAL_REVIEW")

    def test_reconstruct_source_profile(
        self, seeded_factory: LearningServiceFactory
    ):
        """Source quality profile is reconstructible after feedback."""
        source = "audit-source"

        record_approve(
            seeded_factory,
            topic_id="audit-topic-4",
            source_name=source,
            title="Audit Article 4",
        )

        profile = seeded_factory.source_quality_repo.find_by_source_name(source)
        assert profile.is_success
        assert profile.value.total_decisions >= 1
        assert profile.value.approval_rate >= 0.0

    def test_full_reconstruction_chain(
        self, seeded_factory: LearningServiceFactory
    ):
        """All components reconstruct coherently from persisted data."""
        source = "full-audit"

        record_approve(
            seeded_factory,
            topic_id="full-audit-topic",
            source_name=source,
            title="Full Audit Article",
            features={"final_score": 0.75, "base_score": 0.7},
        )

        # Reconstruct all
        pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name=source)
        )
        expl = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        rec = seeded_factory.recommendation_service.recommend(
            source_name=source
        )
        profile = seeded_factory.source_quality_repo.find_by_source_name(source)

        assert pred.is_success
        assert expl.is_success
        assert rec.is_success
        assert profile.is_success

        # Cross-check coherence
        assert rec.value.probability == pred.value.probability
        assert profile.value.approval_rate == 1.0
