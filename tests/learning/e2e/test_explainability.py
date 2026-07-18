"""
Explainability Tests — Every recommendation has explanation,
every prediction has confidence, every explanation has all factors.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.queries.prediction_queries import PredictApprovalQuery

from tests.learning.e2e.conftest import record_approve


class TestExplainability:
    """Verify all outputs include reasoning and confidence."""

    def test_every_recommendation_has_explanation(
        self, seeded_factory: LearningServiceFactory
    ):
        """No recommendation without explanation."""
        result = seeded_factory.recommendation_service.recommend(
            source_name="test"
        )
        assert result.is_success
        assert len(result.value.reasoning) > 0
        # At least one reasoning item should be non-empty
        assert any(len(r) > 0 for r in result.value.reasoning)

    def test_every_prediction_has_confidence(
        self, seeded_factory: LearningServiceFactory
    ):
        """No prediction without confidence."""
        result = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="test")
        )
        assert result.is_success
        assert 0.0 <= result.value.confidence <= 1.0

    def test_explanation_has_all_factors(
        self, seeded_factory: LearningServiceFactory
    ):
        """Explanation includes all scoring factors."""
        result = seeded_factory.explanation_service.explain_decision(
            source_name="test"
        )
        assert result.is_success
        dto = result.value
        assert 0.0 <= dto.base_score <= 1.0
        assert 0.0 <= dto.source_bonus <= 1.0
        assert 0.0 <= dto.final_score <= 1.0
        assert dto.model_version  # non-empty
        assert isinstance(dto.active_signals, tuple)

    def test_recommendation_includes_model_version(
        self, seeded_factory: LearningServiceFactory
    ):
        """Recommendation includes model version for auditability."""
        result = seeded_factory.recommendation_service.recommend(
            source_name="test"
        )
        assert result.is_success
        assert result.value.model_version  # non-empty string

    def test_recommendation_includes_source_quality(
        self, seeded_factory: LearningServiceFactory
    ):
        """Recommendation includes source quality rate."""
        record_approve(
            seeded_factory,
            topic_id="expl-1",
            source_name="explained-source",
            title="Explained Article",
        )

        result = seeded_factory.recommendation_service.recommend(
            source_name="explained-source"
        )
        assert result.is_success
        assert result.value.source_quality == 1.0

    def test_prediction_has_reasoning_summary(
        self, seeded_factory: LearningServiceFactory
    ):
        """Prediction includes a human-readable reasoning summary."""
        result = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="test")
        )
        assert result.is_success
        assert len(result.value.reasoning_summary) > 0

    def test_explanation_with_features_has_correct_scores(
        self, seeded_factory: LearningServiceFactory
    ):
        """Explanation uses provided features for score breakdown."""
        result = seeded_factory.explanation_service.explain_decision(
            source_name="test",
            feature_snapshot=None,  # Reconstructs from current data
        )
        assert result.is_success
        # With no feedback, source_bonus should be 0
        assert result.value.source_bonus == 0.0
