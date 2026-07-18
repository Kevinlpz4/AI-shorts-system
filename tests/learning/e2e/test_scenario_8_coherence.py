"""
Scenario 8: Prediction-Explanation-Recommendation Coherence

Validates that prediction, explanation, and recommendation services
use the same underlying data and produce coherent results.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.queries.prediction_queries import PredictApprovalQuery

from tests.learning.e2e.conftest import record_approve


class TestCoherence:
    """Verify coherence between prediction, explanation, and recommendation."""

    def test_recommendation_uses_prediction_probability(
        self, seeded_factory: LearningServiceFactory
    ):
        """RecommendationDTO.probability matches PredictionDTO.probability."""
        source = "coherent-source"

        # Record some feedback so source quality is non-zero
        record_approve(
            seeded_factory,
            topic_id="coh-1",
            source_name=source,
            title="Coherent Article",
        )

        prediction = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name=source)
        )
        explanation = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        recommendation = seeded_factory.recommendation_service.recommend(
            source_name=source
        )

        assert prediction.is_success
        assert explanation.is_success
        assert recommendation.is_success

        # Recommendation uses prediction's probability
        assert recommendation.value.probability == prediction.value.probability

    def test_explanation_has_all_factors(
        self, seeded_factory: LearningServiceFactory
    ):
        """ExplanationDTO includes all scoring factors."""
        source = "explain-source"

        record_approve(
            seeded_factory,
            topic_id="exp-1",
            source_name=source,
            title="Explain Article",
        )

        explanation = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        assert explanation.is_success
        dto = explanation.value

        # All score fields should be in [0.0, 1.0]
        assert 0.0 <= dto.base_score <= 1.0
        assert 0.0 <= dto.source_bonus <= 1.0
        assert 0.0 <= dto.final_score <= 1.0
        assert dto.source_name == source

    def test_all_three_services_read_same_model(
        self, seeded_factory: LearningServiceFactory
    ):
        """Prediction, explanation, and recommendation all use the same model version."""
        source = "version-source"

        pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name=source)
        )
        expl = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        rec = seeded_factory.recommendation_service.recommend(
            source_name=source
        )

        assert pred.is_success
        assert expl.is_success
        assert rec.is_success

        # All should reference the same model version (v1.0.0 from seeded_factory)
        assert "1.0.0" in expl.value.model_version
        assert "1.0.0" in rec.value.model_version
