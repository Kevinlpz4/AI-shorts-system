"""
Scenario 9: Full Pipeline Integration

Integration Event → Pipeline → Application → Persistence → Presentation

Validates end-to-end flow from feedback ingestion through analytics.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.domain.entities.ids import FeedbackId

from tests.learning.e2e.conftest import record_approve


class TestFullPipelineIntegration:
    """Verify the full pipeline from feedback to analytics."""

    def test_feedback_to_analytics_pipeline(
        self, seeded_factory: LearningServiceFactory
    ):
        """Record feedback → verify persistence → verify source quality → verify analytics."""
        # 1. Record feedback (simulating ingestion event)
        result = record_approve(
            seeded_factory,
            topic_id="integration-topic",
            source_name="integration-source",
            title="Integration Test Article",
            features={"final_score": 0.85, "base_score": 0.7},
        )
        assert result.is_success

        # 2. Verify persistence
        fb_id = FeedbackId.from_string(result.value.id)
        assert seeded_factory.feedback_repo.find_by_id(fb_id).is_success

        # 3. Verify source quality updated
        profile = seeded_factory.source_quality_repo.find_by_source_name(
            "integration-source"
        )
        assert profile.is_success
        assert profile.value.total_decisions == 1
        assert profile.value.approved_count == 1

        # 4. Verify analytics reflect the feedback
        analytics = seeded_factory.analytics_service.execute_get_analytics(
            GetAnalyticsQuery()
        )
        assert analytics.is_success
        assert analytics.value.total_feedback >= 1

    def test_event_publisher_receives_events(
        self, seeded_factory: LearningServiceFactory
    ):
        """Domain events are published after commit."""
        record_approve(
            seeded_factory,
            topic_id="event-topic",
            source_name="event-source",
            title="Event Article",
        )

        # InMemoryLearningEventPublisher stores published events
        events = seeded_factory.event_publisher._events
        assert len(events) >= 1

    def test_uow_commits_correctly(self, seeded_factory: LearningServiceFactory):
        """UnitOfWork commits without error."""
        result = record_approve(
            seeded_factory,
            topic_id="uow-topic",
            source_name="uow-source",
            title="UoW Article",
        )
        assert result.is_success

        # Verify UoW committed (feedback was saved)
        fb_id = FeedbackId.from_string(result.value.id)
        assert seeded_factory.feedback_repo.find_by_id(fb_id).is_success

    def test_multiple_feedbacks_different_sources(
        self, seeded_factory: LearningServiceFactory
    ):
        """Multiple feedback records across different sources are all persisted."""
        sources = ["src-a", "src-b", "src-c"]
        for source in sources:
            result = record_approve(
                seeded_factory,
                topic_id=f"multi-{source}",
                source_name=source,
                title=f"Article from {source}",
            )
            assert result.is_success

        # Verify all 3 sources have profiles
        for source in sources:
            profile = seeded_factory.source_quality_repo.find_by_source_name(source)
            assert profile.is_success
            assert profile.value.total_decisions == 1
