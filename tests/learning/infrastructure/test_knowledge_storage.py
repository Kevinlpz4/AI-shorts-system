"""
Tests for Knowledge Timeline Storage — append-only persistence for snapshots.

Covers:
- KnowledgeTimelineStorage append, append_batch, get_timeline, get_all_for_entity,
  aggregate, snapshot_count
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.integration.observability.knowledge_timeline import KnowledgeSnapshot
from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(
    *,
    entity_type: str = "source",
    entity_id: str = "reuters",
    metric_name: str = "approval_rate",
    metric_value: float = 0.85,
    snapshot_at: datetime | None = None,
) -> KnowledgeSnapshot:
    """Create a KnowledgeSnapshot with sensible defaults."""
    return KnowledgeSnapshot(
        entity_type=entity_type,
        entity_id=entity_id,
        metric_name=metric_name,
        metric_value=metric_value,
        sample_size=10,
        snapshot_at=snapshot_at or datetime(2026, 7, 15, tzinfo=timezone.utc),
    )


# ===========================================================================
# KnowledgeTimelineStorage
# ===========================================================================


class TestKnowledgeTimelineStorageAppend:
    """Tests for append and append_batch operations."""

    def test_append_single(self) -> None:
        """append stores a single snapshot."""
        storage = KnowledgeTimelineStorage()
        snapshot = _make_snapshot()

        storage.append(snapshot)

        assert storage.snapshot_count() == 1

    def test_append_batch(self) -> None:
        """append_batch stores multiple snapshots at once."""
        storage = KnowledgeTimelineStorage()
        snapshots = [_make_snapshot(metric_value=v) for v in [0.1, 0.2, 0.3]]

        storage.append_batch(snapshots)

        assert storage.snapshot_count() == 3


class TestKnowledgeTimelineStorageGetTimeline:
    """Tests for get_timeline retrieval and sorting."""

    def test_get_timeline(self) -> None:
        """get_timeline returns KnowledgeEvolution with matching snapshots."""
        ts1 = datetime(2026, 7, 1, tzinfo=timezone.utc)
        ts2 = datetime(2026, 7, 15, tzinfo=timezone.utc)
        storage = KnowledgeTimelineStorage()
        storage.append(_make_snapshot(metric_value=0.7, snapshot_at=ts1))
        storage.append(_make_snapshot(metric_value=0.85, snapshot_at=ts2))

        evolution = storage.get_timeline("source", "reuters", "approval_rate")

        assert evolution.entity_type == "source"
        assert evolution.entity_id == "reuters"
        assert evolution.metric_name == "approval_rate"
        assert len(evolution.snapshots) == 2
        assert evolution.latest_value() == 0.85

    def test_get_timeline_empty(self) -> None:
        """get_timeline returns empty evolution when no snapshots match."""
        storage = KnowledgeTimelineStorage()

        evolution = storage.get_timeline("source", "reuters", "approval_rate")

        assert len(evolution.snapshots) == 0
        assert evolution.latest_value() == 0.0

    def test_get_timeline_sorted(self) -> None:
        """Snapshots in timeline are sorted chronologically (oldest first)."""
        ts_early = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ts_mid = datetime(2026, 6, 1, tzinfo=timezone.utc)
        ts_late = datetime(2026, 12, 31, tzinfo=timezone.utc)

        storage = KnowledgeTimelineStorage()
        # Insert in reverse chronological order
        storage.append(_make_snapshot(metric_value=0.9, snapshot_at=ts_late))
        storage.append(_make_snapshot(metric_value=0.5, snapshot_at=ts_early))
        storage.append(_make_snapshot(metric_value=0.7, snapshot_at=ts_mid))

        evolution = storage.get_timeline("source", "reuters", "approval_rate")

        values = [s.metric_value for s in evolution.snapshots]
        assert values == [0.5, 0.7, 0.9]


class TestKnowledgeTimelineStorageGetAll:
    """Tests for get_all_for_entity."""

    def test_get_all_for_entity(self) -> None:
        """get_all_for_entity returns all snapshots across metrics for an entity."""
        storage = KnowledgeTimelineStorage()
        storage.append(_make_snapshot(metric_name="approval_rate", metric_value=0.8))
        storage.append(_make_snapshot(metric_name="quality_score", metric_value=0.9))
        # Different entity
        storage.append(_make_snapshot(entity_id="bbc", metric_name="approval_rate", metric_value=0.7))

        results = storage.get_all_for_entity("source", "reuters")

        assert len(results) == 2
        assert all(s.entity_id == "reuters" for s in results)

    def test_get_all_for_entity_none_match(self) -> None:
        """get_all_for_entity returns empty list when no entity matches."""
        storage = KnowledgeTimelineStorage()
        storage.append(_make_snapshot(entity_id="bbc"))

        results = storage.get_all_for_entity("source", "reuters")
        assert results == []


class TestKnowledgeTimelineStorageAggregate:
    """Tests for aggregate operation."""

    def test_aggregate(self) -> None:
        """aggregate computes average metric value per entity."""
        storage = KnowledgeTimelineStorage()
        # reuters: two snapshots → average = (0.8 + 0.6) / 2 = 0.7
        storage.append(_make_snapshot(entity_id="reuters", metric_value=0.8))
        storage.append(_make_snapshot(entity_id="reuters", metric_value=0.6))
        # bbc: one snapshot → average = 0.9
        storage.append(_make_snapshot(entity_id="bbc", metric_value=0.9))

        result = storage.aggregate("source", "approval_rate")

        assert result["reuters"] == pytest.approx(0.7)
        assert result["bbc"] == pytest.approx(0.9)

    def test_aggregate_empty(self) -> None:
        """aggregate returns empty dict when no snapshots match."""
        storage = KnowledgeTimelineStorage()
        result = storage.aggregate("source", "nonexistent_metric")
        assert result == {}


class TestKnowledgeTimelineStorageCount:
    """Tests for snapshot_count."""

    def test_snapshot_count(self) -> None:
        """snapshot_count returns the total number of stored snapshots."""
        storage = KnowledgeTimelineStorage()
        assert storage.snapshot_count() == 0

        storage.append(_make_snapshot())
        assert storage.snapshot_count() == 1

        storage.append_batch([_make_snapshot(), _make_snapshot()])
        assert storage.snapshot_count() == 3
