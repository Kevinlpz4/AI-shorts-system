"""
Scenario 11: Source Quality Timeline Trend

Validates KnowledgeEvolution trend detection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage
from learning.integration.observability.knowledge_timeline import KnowledgeSnapshot


class TestSourceQualityTimelineTrend:
    """Verify KnowledgeEvolution.trend() detects improving sources."""

    def test_improving_trend(self):
        """Increasing values → IMPROVING trend."""
        storage = KnowledgeTimelineStorage()

        values = [0.70, 0.75, 0.83, 0.91]
        dates = [
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
            datetime(2026, 3, 1, tzinfo=timezone.utc),
            datetime(2026, 4, 1, tzinfo=timezone.utc),
        ]

        for val, dt in zip(values, dates):
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id="improving-source",
                    metric_name="approval_rate",
                    metric_value=val,
                    sample_size=50,
                    snapshot_at=dt,
                )
            )

        evolution = storage.get_timeline(
            "source", "improving-source", "approval_rate"
        )
        assert evolution.latest_value() == 0.91
        assert evolution.trend() == "IMPROVING"

    def test_declining_trend(self):
        """Decreasing values → DECLINING trend."""
        storage = KnowledgeTimelineStorage()

        values = [0.90, 0.85, 0.80, 0.70]
        dates = [
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
            datetime(2026, 3, 1, tzinfo=timezone.utc),
            datetime(2026, 4, 1, tzinfo=timezone.utc),
        ]

        for val, dt in zip(values, dates):
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id="declining-source",
                    metric_name="approval_rate",
                    metric_value=val,
                    sample_size=50,
                    snapshot_at=dt,
                )
            )

        evolution = storage.get_timeline(
            "source", "declining-source", "approval_rate"
        )
        assert evolution.latest_value() == 0.70
        assert evolution.trend() == "DECLINING"

    def test_stable_trend(self):
        """Constant values → STABLE trend."""
        storage = KnowledgeTimelineStorage()

        for i in range(4):
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id="stable-source",
                    metric_name="approval_rate",
                    metric_value=0.80,
                    sample_size=50,
                    snapshot_at=datetime(2026, i + 1, 1, tzinfo=timezone.utc),
                )
            )

        evolution = storage.get_timeline(
            "source", "stable-source", "approval_rate"
        )
        assert evolution.trend() == "STABLE"

    def test_insufficient_data_trend(self):
        """Less than 2 snapshots → INSUFFICIENT_DATA."""
        storage = KnowledgeTimelineStorage()

        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="solo-source",
                metric_name="approval_rate",
                metric_value=0.80,
                sample_size=10,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )

        evolution = storage.get_timeline(
            "source", "solo-source", "approval_rate"
        )
        assert evolution.trend() == "INSUFFICIENT_DATA"

    def test_period(self):
        """period() returns the time range of snapshots."""
        storage = KnowledgeTimelineStorage()

        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 15, tzinfo=timezone.utc)

        storage.append(
            KnowledgeSnapshot(
                entity_type="source", entity_id="s",
                metric_name="m", metric_value=0.5, sample_size=10,
                snapshot_at=t1,
            )
        )
        storage.append(
            KnowledgeSnapshot(
                entity_type="source", entity_id="s",
                metric_name="m", metric_value=0.6, sample_size=10,
                snapshot_at=t2,
            )
        )

        evolution = storage.get_timeline("source", "s", "m")
        period = evolution.period()
        assert period is not None
        assert period[0] == t1
        assert period[1] == t2
