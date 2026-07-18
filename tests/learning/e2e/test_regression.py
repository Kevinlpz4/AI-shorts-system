"""
Regression Tests — Full suite regression.

Smoke tests that exercise the most critical paths to catch
regressions across all Learning BC components.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.application.queries.prediction_queries import (
    PredictApprovalQuery,
    ExplainScoreQuery,
)
from learning.domain.entities.ids import FeedbackId

from tests.learning.e2e.conftest import record_approve, record_reject


class TestRegression:
    """Smoke tests covering critical Learning BC paths."""

    def test_factory_creates_all_services(self):
        """LearningServiceFactory creates all services correctly."""
        factory = LearningServiceFactory()

        assert factory.decision_service is not None
        assert factory.signal_service is not None
        assert factory.scoring_service is not None
        assert factory.prediction_service is not None
        assert factory.explanation_service is not None
        assert factory.recommendation_service is not None
        assert factory.analytics_service is not None
        assert factory.dataset_service is not None

    def test_factory_build_all(self):
        """build_all returns dictionary with all services."""
        factory = LearningServiceFactory()
        services = factory.build_all()

        expected_keys = {
            "decision_service",
            "signal_service",
            "scoring_service",
            "dataset_service",
            "analytics_service",
            "prediction_service",
            "explanation_service",
            "recommendation_service",
        }
        assert set(services.keys()) == expected_keys

    def test_regression_approve_then_predict(self, seeded_factory: LearningServiceFactory):
        """Approve feedback → prediction reflects source quality."""
        for i in range(5):
            record_approve(
                seeded_factory,
                topic_id=f"reg-approve-{i}",
                source_name="reg-source",
                title=f"Good {i}",
            )

        pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="reg-source")
        )
        assert pred.is_success
        # With 100% approval and 5 samples, confidence > 0
        assert pred.value.confidence > 0.0

    def test_regression_reject_then_recommend(
        self, seeded_factory: LearningServiceFactory
    ):
        """Reject feedback → recommendation reflects poor source."""
        for i in range(10):
            record_reject(
                seeded_factory,
                topic_id=f"reg-reject-{i}",
                source_name="bad-reg-source",
                title=f"Bad {i}",
                reason="Spam",
            )

        rec = seeded_factory.recommendation_service.recommend(
            source_name="bad-reg-source"
        )
        assert rec.is_success
        assert rec.value.recommendation == "REJECT"

    def test_regression_full_lifecycle(self, seeded_factory: LearningServiceFactory):
        """Complete lifecycle: feedback → profile → prediction → recommendation → analytics → dataset."""
        source = "lifecycle-src"

        # Feedback
        for i in range(5):
            record_approve(
                seeded_factory,
                topic_id=f"lc-{i}",
                source_name=source,
                title=f"Article {i}",
                features={"final_score": 0.8},
            )

        # Profile
        profile = seeded_factory.source_quality_repo.find_by_source_name(source)
        assert profile.is_success
        assert profile.value.approval_rate == 1.0

        # Prediction
        pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name=source)
        )
        assert pred.is_success

        # Explanation
        expl = seeded_factory.explanation_service.explain_decision(
            source_name=source
        )
        assert expl.is_success

        # Recommendation (with features to get higher probability)
        rec = seeded_factory.recommendation_service.recommend(
            source_name=source,
            features={"final_score": 0.9},
        )
        assert rec.is_success
        assert rec.value.recommendation in ("APPROVE", "MANUAL_REVIEW")

        # Analytics
        analytics = seeded_factory.analytics_service.execute_get_analytics(
            GetAnalyticsQuery()
        )
        assert analytics.is_success
        assert analytics.value.total_feedback >= 5

        # Dataset
        ds = seeded_factory.dataset_service.execute_generate_dataset(
            GenerateDatasetCommand(
                name="Lifecycle dataset",
                time_window_start="2020-01-01T00:00:00Z",
                time_window_end="2030-12-31T23:59:59Z",
            )
        )
        assert ds.is_success
        assert ds.value.sample_count >= 5

    def test_regression_multiple_sources(
        self, seeded_factory: LearningServiceFactory
    ):
        """Multiple sources tracked independently."""
        for i in range(10):
            record_approve(
                seeded_factory,
                topic_id=f"ms-a-{i}",
                source_name="ms-source-a",
                title=f"Good A {i}",
            )
        for i in range(10):
            record_reject(
                seeded_factory,
                topic_id=f"ms-b-{i}",
                source_name="ms-source-b",
                title=f"Bad B {i}",
                reason="Spam",
            )

        profile_a = seeded_factory.source_quality_repo.find_by_source_name("ms-source-a")
        profile_b = seeded_factory.source_quality_repo.find_by_source_name("ms-source-b")

        assert profile_a.value.approval_rate == 1.0
        assert profile_b.value.approval_rate == 0.0

    def test_regression_feedback_persists_correctly(
        self, seeded_factory: LearningServiceFactory
    ):
        """FeedbackRecord is persisted with all fields intact."""
        result = record_approve(
            seeded_factory,
            topic_id="persist-topic",
            source_name="persist-source",
            title="Persist Article",
            features={"final_score": 0.88, "base_score": 0.77},
        )
        assert result.is_success

        fb_id = FeedbackId.from_string(result.value.id)
        record = seeded_factory.feedback_repo.find_by_id(fb_id).value

        assert record.topic_id == "persist-topic"
        assert record.source_name == "persist-source"
        assert record.title == "Persist Article"
        assert record.feature_snapshot.final_score == pytest.approx(0.88)
        assert record.feature_snapshot.base_score == pytest.approx(0.77)

    def test_regression_explain_score_query(
        self, seeded_factory: LearningServiceFactory
    ):
        """ExplainScoreQuery works through prediction_service."""
        record_approve(
            seeded_factory,
            topic_id="esq-1",
            source_name="esq-source",
            title="ESQ Article",
        )

        result = seeded_factory.prediction_service.execute_explain_score(
            ExplainScoreQuery(source_name="esq-source")
        )
        assert result.is_success
        dto = result.value
        assert dto.source_name == "esq-source"
        assert 0.0 <= dto.source_bonus <= 1.0
