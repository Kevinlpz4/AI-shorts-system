"""
Performance Tests — p95 latency measurements.

These tests measure (don't optimize) the performance of key operations.
All operations use in-memory stores, so p95 should be well under limits.
"""
from __future__ import annotations

import time

import pytest

from learning.infrastructure.composition import LearningServiceFactory
from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.application.queries.prediction_queries import PredictApprovalQuery
from learning.integration.observability.knowledge_timeline import KnowledgeSnapshot
from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage

from datetime import datetime, timezone


@pytest.mark.performance
class TestPerformance:
    """Measure p95 latency for key operations."""

    def test_prediction_p95(self, seeded_factory: LearningServiceFactory):
        """Prediction p95 < 100ms."""
        times = []
        for _ in range(20):
            start = time.perf_counter()
            seeded_factory.prediction_service.execute_predict_approval(
                PredictApprovalQuery(source_name="perf-source")
            )
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 100, f"Prediction p95: {p95:.2f}ms (limit: 100ms)"

    def test_recommendation_p95(self, seeded_factory: LearningServiceFactory):
        """Recommendation p95 < 100ms."""
        times = []
        for _ in range(20):
            start = time.perf_counter()
            seeded_factory.recommendation_service.recommend(
                source_name="perf-source"
            )
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 100, f"Recommendation p95: {p95:.2f}ms (limit: 100ms)"

    def test_feedback_p95(self, seeded_factory: LearningServiceFactory):
        """Feedback p95 < 100ms."""
        times = []
        for i in range(20):
            start = time.perf_counter()
            seeded_factory.decision_service.execute_record_feedback(
                RecordFeedbackCommand(
                    topic_id=f"perf-{i}",
                    decision="APPROVED",
                    reason=None,
                    source_name="perf-source",
                    title=f"Perf {i}",
                )
            )
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 100, f"Feedback p95: {p95:.2f}ms (limit: 100ms)"

    def test_timeline_query_p95(self):
        """Timeline query p95 < 100ms."""
        storage = KnowledgeTimelineStorage()
        # Seed with data
        for i in range(100):
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id=f"src-{i}",
                    metric_name="approval_rate",
                    metric_value=0.8,
                    sample_size=10,
                    snapshot_at=datetime.now(timezone.utc),
                )
            )

        times = []
        for _ in range(20):
            start = time.perf_counter()
            storage.get_timeline("source", "src-50", "approval_rate")
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 100, f"Timeline p95: {p95:.2f}ms (limit: 100ms)"

    def test_analytics_p95(self, seeded_factory: LearningServiceFactory):
        """Analytics p95 < 150ms."""
        times = []
        for _ in range(20):
            start = time.perf_counter()
            seeded_factory.analytics_service.execute_get_analytics(
                GetAnalyticsQuery()
            )
            times.append((time.perf_counter() - start) * 1000)
        times.sort()
        p95 = times[int(len(times) * 0.95)]
        assert p95 < 150, f"Analytics p95: {p95:.2f}ms (limit: 150ms)"
