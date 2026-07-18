"""
Scenario 1: Complete Learning Cycle

RawArticle → Research → Prediction → Recommendation → Feedback APPROVE →
FeedbackRecord persisted → LearningSignal updated → KnowledgeSnapshot created →
KnowledgeTimeline updated → Dataset Metadata available
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.application.queries.prediction_queries import PredictApprovalQuery
from learning.domain.entities.ids import FeedbackId

from tests.learning.e2e.conftest import record_approve


class TestCompleteLearningCycle:
    """Validate the full learning cycle from prediction through feedback."""

    def test_prediction_before_feedback(self, seeded_factory: LearningServiceFactory):
        """Prediction works on a freshly seeded source."""
        result = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="reuters", features={"final_score": 0.8})
        )
        assert result.is_success
        prediction = result.value
        assert 0.0 <= prediction.probability <= 1.0
        assert 0.0 <= prediction.confidence <= 1.0
        assert len(prediction.reasoning_summary) > 0

    def test_recommendation_before_feedback(self, seeded_factory: LearningServiceFactory):
        """Recommendation works on a freshly seeded source."""
        result = seeded_factory.recommendation_service.recommend(
            source_name="reuters", features={"final_score": 0.8}
        )
        assert result.is_success
        rec = result.value
        assert rec.recommendation in ("APPROVE", "REJECT", "MANUAL_REVIEW")
        assert len(rec.reasoning) > 0

    def test_full_cycle_predict_then_feedback(self, seeded_factory: LearningServiceFactory):
        """Complete cycle: predict → get recommendation → record feedback → verify persistence."""
        # Step 1: Predict
        pred_result = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="reuters", features={"final_score": 0.8})
        )
        assert pred_result.is_success

        # Step 2: Get recommendation
        rec_result = seeded_factory.recommendation_service.recommend(
            source_name="reuters", features={"final_score": 0.8}
        )
        assert rec_result.is_success

        # Step 3: Record feedback
        fb_result = record_approve(
            seeded_factory,
            topic_id="topic-1",
            source_name="reuters",
            title="Test Article",
            features={"final_score": 0.8, "base_score": 0.7},
        )
        assert fb_result.is_success
        fb_dto = fb_result.value
        assert fb_dto.decision == "APPROVED"
        assert fb_dto.source_name == "reuters"

        # Step 4: Verify FeedbackRecord persisted
        feedback_id = FeedbackId.from_string(fb_dto.id)
        find_result = seeded_factory.feedback_repo.find_by_id(feedback_id)
        assert find_result.is_success

        # Step 5: Verify SourceQualityProfile updated
        source_result = seeded_factory.source_quality_repo.find_by_source_name("reuters")
        assert source_result.is_success
        assert source_result.value.total_decisions >= 1
        assert source_result.value.approved_count >= 1

        # Step 6: Verify prediction still works after feedback
        new_pred = seeded_factory.prediction_service.execute_predict_approval(
            PredictApprovalQuery(source_name="reuters")
        )
        assert new_pred.is_success

    def test_feedback_persists_feature_snapshot(
        self, seeded_factory: LearningServiceFactory
    ):
        """Feedback persists the FeatureSnapshot at decision time."""
        fb_result = record_approve(
            seeded_factory,
            topic_id="topic-feat",
            source_name="reuters",
            title="Article with features",
            features={"final_score": 0.9, "base_score": 0.8},
        )
        assert fb_result.is_success

        # Verify via query
        fb_id = FeedbackId.from_string(fb_result.value.id)
        detail = seeded_factory.feedback_repo.find_by_id(fb_id).value
        assert detail.feature_snapshot.final_score == pytest.approx(0.9)
        assert detail.feature_snapshot.base_score == pytest.approx(0.8)
