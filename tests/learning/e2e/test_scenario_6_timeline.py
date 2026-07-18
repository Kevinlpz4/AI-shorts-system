"""
Scenario 6: Knowledge Timeline (Append-Only)

Validates KnowledgeTimelineStorage append-only semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage
from learning.integration.observability.knowledge_timeline import KnowledgeSnapshot


class TestKnowledgeTimeline:
    """Verify KnowledgeTimelineStorage is append-only and ordered."""

    def test_append_and_retrieve(self):
        """Append snapshots and retrieve them chronologically."""
        storage = KnowledgeTimelineStorage()

        timestamps = [
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
            datetime(2026, 3, 1, tzinfo=timezone.utc),
        ]

        for ts in timestamps:
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id="reuters",
                    metric_name="approval_rate",
                    metric_value=0.7,
                    sample_size=10,
                    snapshot_at=ts,
                )
            )

        # Verify append-only: 3 snapshots, ordered
        assert storage.snapshot_count() == 3

        evolution = storage.get_timeline("source", "reuters", "approval_rate")
        assert len(evolution.snapshots) == 3
        assert evolution.snapshots[0].snapshot_at < evolution.snapshots[1].snapshot_at
        assert evolution.snapshots[1].snapshot_at < evolution.snapshots[2].snapshot_at

    def test_get_timeline_filters_correctly(self):
        """Timeline only returns matching entity_type/entity_id/metric_name."""
        storage = KnowledgeTimelineStorage()

        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="reuters",
                metric_name="approval_rate",
                metric_value=0.8,
                sample_size=10,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="bbc",
                metric_name="approval_rate",
                metric_value=0.9,
                sample_size=5,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="reuters",
                metric_name="quality_score",
                metric_value=0.75,
                sample_size=8,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )

        # Only reuters + approval_rate
        evolution = storage.get_timeline("source", "reuters", "approval_rate")
        assert len(evolution.snapshots) == 1
        assert evolution.snapshots[0].metric_value == 0.8

    def test_append_batch(self):
        """Batch append works correctly."""
        storage = KnowledgeTimelineStorage()

        snapshots = [
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="src",
                metric_name="rate",
                metric_value=float(i) / 10,
                sample_size=i,
                snapshot_at=datetime(2026, i + 1, 1, tzinfo=timezone.utc),
            )
            for i in range(1, 6)
        ]

        storage.append_batch(snapshots)
        assert storage.snapshot_count() == 5

    def test_empty_timeline(self):
        """Empty storage returns empty evolution."""
        storage = KnowledgeTimelineStorage()
        evolution = storage.get_timeline("source", "unknown", "metric")
        assert len(evolution.snapshots) == 0
        assert evolution.latest_value() == 0.0

    def test_aggregate(self):
        """Aggregation computes average per entity."""
        storage = KnowledgeTimelineStorage()

        for val in [0.6, 0.8]:
            storage.append(
                KnowledgeSnapshot(
                    entity_type="source",
                    entity_id="reuters",
                    metric_name="approval_rate",
                    metric_value=val,
                    sample_size=10,
                    snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                )
            )
        storage.append(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="bbc",
                metric_name="approval_rate",
                metric_value=0.9,
                sample_size=5,
                snapshot_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )

        result = storage.aggregate("source", "approval_rate")
        assert result["reuters"] == pytest.approx(0.7)
        assert result["bbc"] == pytest.approx(0.9)
