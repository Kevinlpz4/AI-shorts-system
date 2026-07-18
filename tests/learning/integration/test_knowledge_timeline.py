"""
Tests for KnowledgeTimeline — KnowledgeSnapshot, KnowledgeEvolution, KnowledgeTimelineCollector.

Validates: snapshot collection, timeline retrieval, trend calculation,
latest value, period, and snapshot count.
"""
from __future__ import annotations

from datetime import datetime, timezone

from learning.integration.observability.knowledge_timeline import (
    KnowledgeEvolution,
    KnowledgeSnapshot,
    KnowledgeTimelineCollector,
)


def _ts(year: int, month: int, day: int) -> datetime:
    """Helper to create a fixed UTC datetime."""
    return datetime(year, month, day, tzinfo=timezone.utc)


# ─── KnowledgeSnapshot ────────────────────────────────────────────────

class TestKnowledgeSnapshot:
    """Point-in-time snapshot of knowledge about an entity."""

    def test_construction_defaults(self) -> None:
        snap = KnowledgeSnapshot()
        assert snap.entity_type == ""
        assert snap.entity_id == ""
        assert snap.metric_name == ""
        assert snap.metric_value == 0.0
        assert snap.sample_size == 0
        assert snap.snapshot_at is not None
        assert snap.metadata == {}

    def test_construction_all_fields(self) -> None:
        ts = _ts(2026, 7, 15)
        snap = KnowledgeSnapshot(
            entity_type="source",
            entity_id="Reuters",
            metric_name="approval_rate",
            metric_value=0.85,
            sample_size=100,
            snapshot_at=ts,
            metadata={"model_version": "1.0"},
        )
        assert snap.entity_type == "source"
        assert snap.entity_id == "Reuters"
        assert snap.metric_name == "approval_rate"
        assert snap.metric_value == 0.85
        assert snap.sample_size == 100
        assert snap.snapshot_at == ts
        assert snap.metadata == {"model_version": "1.0"}

    def test_frozen(self) -> None:
        snap = KnowledgeSnapshot(entity_id="Reuters")
        # frozen=True — setattr will raise
        try:
            snap.entity_id = "changed"  # type: ignore[misc]
            # If no error, the snapshot is not frozen (but dataclass(frozen=True) should raise)
            assert False, "Expected AttributeError for frozen dataclass"
        except AttributeError:
            pass


# ─── KnowledgeEvolution ───────────────────────────────────────────────

class TestKnowledgeEvolution:
    """Tracks how a metric evolved over time."""

    def _make_evolution(self, values: list[float], timestamps: list[datetime] | None = None) -> KnowledgeEvolution:
        """Helper to build KnowledgeEvolution with snapshots at given values."""
        if timestamps is None:
            timestamps = [_ts(2026, 1, i + 1) for i in range(len(values))]
        snapshots = tuple(
            KnowledgeSnapshot(
                entity_type="source",
                entity_id="Reuters",
                metric_name="approval_rate",
                metric_value=v,
                snapshot_at=ts,
            )
            for v, ts in zip(values, timestamps)
        )
        return KnowledgeEvolution(
            entity_type="source",
            entity_id="Reuters",
            metric_name="approval_rate",
            snapshots=snapshots,
        )

    def test_trend_improving(self) -> None:
        evo = self._make_evolution([0.5, 0.6, 0.7, 0.8])
        assert evo.trend() == "IMPROVING"

    def test_trend_declining(self) -> None:
        evo = self._make_evolution([0.9, 0.8, 0.7, 0.6])
        assert evo.trend() == "DECLINING"

    def test_trend_stable(self) -> None:
        evo = self._make_evolution([0.7, 0.7, 0.71, 0.72])
        assert evo.trend() == "STABLE"

    def test_trend_stable_within_threshold(self) -> None:
        # Values within 5% of first value → STABLE
        evo = self._make_evolution([1.0, 1.02, 1.04, 1.05])
        assert evo.trend() == "STABLE"

    def test_trend_insufficient_data(self) -> None:
        evo = self._make_evolution([0.8])
        assert evo.trend() == "INSUFFICIENT_DATA"

    def test_trend_insufficient_data_empty(self) -> None:
        evo = KnowledgeEvolution(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", snapshots=()
        )
        assert evo.trend() == "INSUFFICIENT_DATA"

    def test_latest_value(self) -> None:
        evo = self._make_evolution([0.5, 0.6, 0.7])
        assert evo.latest_value() == 0.7

    def test_latest_value_empty(self) -> None:
        evo = KnowledgeEvolution(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", snapshots=()
        )
        assert evo.latest_value() == 0.0

    def test_period(self) -> None:
        timestamps = [_ts(2026, 1, 1), _ts(2026, 6, 15), _ts(2026, 12, 31)]
        evo = self._make_evolution([0.5, 0.7, 0.9], timestamps=timestamps)
        period = evo.period()
        assert period is not None
        assert period[0] == _ts(2026, 1, 1)
        assert period[1] == _ts(2026, 12, 31)

    def test_period_empty(self) -> None:
        evo = KnowledgeEvolution(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", snapshots=()
        )
        assert evo.period() is None

    def test_trend_boundary_exactly_5_percent_up(self) -> None:
        # 1.0 * 1.05 = 1.05 → NOT > 1.05, so STABLE
        evo = self._make_evolution([1.0, 1.05])
        assert evo.trend() == "STABLE"

    def test_trend_boundary_above_5_percent_up(self) -> None:
        # 1.0 * 1.05 = 1.05, 1.06 > 1.05 → IMPROVING
        evo = self._make_evolution([1.0, 1.06])
        assert evo.trend() == "IMPROVING"

    def test_trend_boundary_exactly_5_percent_down(self) -> None:
        # 1.0 * 0.95 = 0.95 → NOT < 0.95, so STABLE
        evo = self._make_evolution([1.0, 0.95])
        assert evo.trend() == "STABLE"

    def test_trend_boundary_below_5_percent_down(self) -> None:
        # 1.0 * 0.95 = 0.95, 0.94 < 0.95 → DECLINING
        evo = self._make_evolution([1.0, 0.94])
        assert evo.trend() == "DECLINING"


# ─── KnowledgeTimelineCollector ───────────────────────────────────────

class TestKnowledgeTimelineCollector:
    """Collects KnowledgeSnapshots and builds timelines."""

    def test_collect_snapshot(self) -> None:
        collector = KnowledgeTimelineCollector()
        snap = KnowledgeSnapshot(
            entity_type="source",
            entity_id="Reuters",
            metric_name="approval_rate",
            metric_value=0.85,
        )
        collector.collect(snap)
        assert collector.snapshot_count() == 1

    def test_get_timeline(self) -> None:
        collector = KnowledgeTimelineCollector()
        snap1 = KnowledgeSnapshot(
            entity_type="source",
            entity_id="Reuters",
            metric_name="approval_rate",
            metric_value=0.7,
            snapshot_at=_ts(2026, 1, 1),
        )
        snap2 = KnowledgeSnapshot(
            entity_type="source",
            entity_id="Reuters",
            metric_name="approval_rate",
            metric_value=0.85,
            snapshot_at=_ts(2026, 6, 15),
        )
        # Add different metric too
        snap3 = KnowledgeSnapshot(
            entity_type="source",
            entity_id="Reuters",
            metric_name="quality_score",
            metric_value=0.6,
            snapshot_at=_ts(2026, 1, 1),
        )
        collector.collect(snap1)
        collector.collect(snap2)
        collector.collect(snap3)

        timeline = collector.get_timeline("source", "Reuters", "approval_rate")
        assert timeline.entity_type == "source"
        assert timeline.entity_id == "Reuters"
        assert timeline.metric_name == "approval_rate"
        assert len(timeline.snapshots) == 2
        assert timeline.snapshots[0].metric_value == 0.7
        assert timeline.snapshots[1].metric_value == 0.85

    def test_get_timeline_empty(self) -> None:
        collector = KnowledgeTimelineCollector()
        timeline = collector.get_timeline("source", "Reuters", "approval_rate")
        assert len(timeline.snapshots) == 0
        assert timeline.entity_type == "source"
        assert timeline.entity_id == "Reuters"
        assert timeline.metric_name == "approval_rate"

    def test_get_timeline_filters_by_entity(self) -> None:
        collector = KnowledgeTimelineCollector()
        collector.collect(KnowledgeSnapshot(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", metric_value=0.8,
        ))
        collector.collect(KnowledgeSnapshot(
            entity_type="source", entity_id="TechBlog", metric_name="approval_rate", metric_value=0.6,
        ))
        timeline = collector.get_timeline("source", "Reuters", "approval_rate")
        assert len(timeline.snapshots) == 1
        assert timeline.snapshots[0].metric_value == 0.8

    def test_get_timeline_filters_by_entity_type(self) -> None:
        collector = KnowledgeTimelineCollector()
        collector.collect(KnowledgeSnapshot(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", metric_value=0.8,
        ))
        collector.collect(KnowledgeSnapshot(
            entity_type="dimension", entity_id="Reuters", metric_name="approval_rate", metric_value=0.6,
        ))
        timeline = collector.get_timeline("source", "Reuters", "approval_rate")
        assert len(timeline.snapshots) == 1

    def test_snapshot_count(self) -> None:
        collector = KnowledgeTimelineCollector()
        assert collector.snapshot_count() == 0
        collector.collect(KnowledgeSnapshot(entity_type="source", entity_id="A", metric_name="x"))
        assert collector.snapshot_count() == 1
        collector.collect(KnowledgeSnapshot(entity_type="source", entity_id="B", metric_name="x"))
        assert collector.snapshot_count() == 2

    def test_snapshot_count_includes_all_metrics(self) -> None:
        collector = KnowledgeTimelineCollector()
        collector.collect(KnowledgeSnapshot(
            entity_type="source", entity_id="Reuters", metric_name="approval_rate", metric_value=0.8,
        ))
        collector.collect(KnowledgeSnapshot(
            entity_type="source", entity_id="Reuters", metric_name="quality_score", metric_value=0.6,
        ))
        assert collector.snapshot_count() == 2
        # But timeline for one metric only shows matching ones
        timeline = collector.get_timeline("source", "Reuters", "approval_rate")
        assert len(timeline.snapshots) == 1

    def test_collect_multiple(self) -> None:
        collector = KnowledgeTimelineCollector()
        snaps = [
            KnowledgeSnapshot(entity_type="source", entity_id="A", metric_name="m", metric_value=v)
            for v in [0.1, 0.2, 0.3, 0.4, 0.5]
        ]
        for s in snaps:
            collector.collect(s)
        assert collector.snapshot_count() == 5
        timeline = collector.get_timeline("source", "A", "m")
        assert len(timeline.snapshots) == 5
