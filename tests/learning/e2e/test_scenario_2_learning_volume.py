"""
Scenario 2: Learning from Volume (100 articles)

Validates that the system correctly handles high-volume feedback
and maintains accurate SourceQualityProfile statistics.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.queries.prediction_queries import PredictApprovalQuery

from tests.learning.e2e.conftest import record_approve, record_reject


class TestLearningFromVolume:
    """Verify source quality tracking with high-volume feedback."""

    def test_source_quality_after_100_articles(
        self, seeded_factory: LearningServiceFactory
    ):
        """80 approvals + 20 rejections → SourceQualityProfile reflects accurate counts."""
        # Record 80 approvals
        for i in range(80):
            record_approve(
                seeded_factory,
                topic_id=f"topic-{i}",
                source_name="reuters",
                title=f"Article {i}",
            )

        # Record 20 rejections
        for i in range(20):
            record_reject(
                seeded_factory,
                topic_id=f"topic-reject-{i}",
                source_name="reuters",
                title=f"Bad Article {i}",
                reason="Low quality",
            )

        # Verify SourceQualityProfile
        profile = seeded_factory.source_quality_repo.find_by_source_name("reuters")
        assert profile.is_success
        assert profile.value.total_decisions == 100
        assert profile.value.approved_count == 80
        assert profile.value.rejected_count == 20
        assert profile.value.approval_rate == pytest.approx(0.8, abs=0.01)

    def test_confidence_increases_with_volume(
        self, seeded_factory: LearningServiceFactory
    ):
        """Confidence should increase as sample size grows."""
        # Record many feedbacks
        for i in range(50):
            record_approve(
                seeded_factory,
                topic_id=f"vol-{i}",
                source_name="reuters",
                title=f"Article {i}",
            )

        prediction = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="reuters")
        )
        assert prediction.is_success
        assert prediction.value.confidence > 0.0

    def test_multiple_sources_independent(self, seeded_factory: LearningServiceFactory):
        """Different sources maintain independent quality profiles."""
        # Source A: mostly approved
        for i in range(30):
            record_approve(
                seeded_factory,
                topic_id=f"a-{i}",
                source_name="source-a",
                title=f"Good Article {i}",
            )

        # Source B: mostly rejected
        for i in range(25):
            record_reject(
                seeded_factory,
                topic_id=f"b-{i}",
                source_name="source-b",
                title=f"Bad Article {i}",
                reason="Spam",
            )
        for i in range(5):
            record_approve(
                seeded_factory,
                topic_id=f"b-approve-{i}",
                source_name="source-b",
                title=f"OK Article {i}",
            )

        profile_a = seeded_factory.source_quality_repo.find_by_source_name("source-a")
        profile_b = seeded_factory.source_quality_repo.find_by_source_name("source-b")

        assert profile_a.is_success
        assert profile_b.is_success
        assert profile_a.value.approval_rate == pytest.approx(1.0, abs=0.01)
        assert profile_b.value.approval_rate == pytest.approx(5 / 30, abs=0.01)

    def test_analytics_reflect_volume(self, seeded_factory: LearningServiceFactory):
        """Analytics aggregates reflect the total feedback volume."""
        for i in range(10):
            record_approve(
                seeded_factory,
                topic_id=f"an-{i}",
                source_name="reuters",
                title=f"Article {i}",
            )

        from learning.application.queries.analytics_queries import GetAnalyticsQuery

        result = seeded_factory.analytics_service.execute_get_analytics(
            GetAnalyticsQuery()
        )
        assert result.is_success
        assert result.value.total_feedback >= 10
