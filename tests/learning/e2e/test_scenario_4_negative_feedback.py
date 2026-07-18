"""
Scenario 4: Negative Feedback Degrades Source

Validates that a high rejection rate degrades source quality
below the 0.5 threshold.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory

from tests.learning.e2e.conftest import record_approve, record_reject


class TestNegativeFeedbackDegradesSource:
    """Verify source quality degrades with negative feedback patterns."""

    def test_source_quality_degrades_below_half(
        self, seeded_factory: LearningServiceFactory
    ):
        """5 approvals + 15 rejections → approval_rate < 0.5."""
        # First: approve some
        for i in range(5):
            record_approve(
                seeded_factory,
                topic_id=f"t-{i}",
                source_name="bad-source",
                title=f"Art {i}",
            )

        # Then: reject many
        for i in range(15):
            record_reject(
                seeded_factory,
                topic_id=f"t-reject-{i}",
                source_name="bad-source",
                title=f"Spam {i}",
                reason="Spam",
            )

        # Verify quality degraded
        profile = seeded_factory.source_quality_repo.find_by_source_name("bad-source")
        assert profile.is_success
        assert profile.value.approval_rate < 0.5
        assert profile.value.total_decisions == 20
        assert profile.value.rejected_count == 15

    def test_prediction_reflects_degraded_source(
        self, seeded_factory: LearningServiceFactory
    ):
        """Prediction probability reflects low source quality."""
        # Degrade the source
        for i in range(3):
            record_approve(
                seeded_factory,
                topic_id=f"dp-{i}",
                source_name="degraded-src",
                title=f"OK {i}",
            )
        for i in range(17):
            record_reject(
                seeded_factory,
                topic_id=f"dr-{i}",
                source_name="degraded-src",
                title=f"Bad {i}",
                reason="Low quality",
            )

        from learning.application.queries.prediction_queries import PredictApprovalQuery

        prediction = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="degraded-src")
        )
        assert prediction.is_success
        # With 15% approval rate, probability should be low
        assert prediction.value.probability < 0.5

    def test_recommendation_rejects_degraded_source(
        self, seeded_factory: LearningServiceFactory
    ):
        """Recommendation should reflect degraded source quality."""
        # Create a degraded source
        for i in range(2):
            record_approve(
                seeded_factory,
                topic_id=f"rr-{i}",
                source_name="rejection-source",
                title=f"OK {i}",
            )
        for i in range(18):
            record_reject(
                seeded_factory,
                topic_id=f"rj-{i}",
                source_name="rejection-source",
                title=f"Spam {i}",
                reason="Spam",
            )

        result = seeded_factory.recommendation_service.recommend(
            source_name="rejection-source"
        )
        assert result.is_success
        # With 10% approval, the recommendation should be REJECT
        assert result.value.recommendation == "REJECT"
        assert result.value.source_quality < 0.5
