"""
Tests for KnowledgeTimelineRepository — append-only guarantee, timeline ordering.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.persistence.repositories.knowledge_timeline_repository import KnowledgeTimelineRepository


class TestKnowledgeTimelineRepositoryAppend:
    def test_append_single(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        snapshot = repo.append(
            entity_type="source",
            entity_id="bbc-news",
            metric_name="approval_rate",
            metric_value=0.85,
            sample_size=50,
            snapshot_at=now,
        )
        session.commit()

        assert snapshot.entity_type == "source"
        assert snapshot.entity_id == "bbc-news"
        assert snapshot.metric_name == "approval_rate"
        assert snapshot.metric_value == 0.85
        assert snapshot.sample_size == 50
        assert snapshot.id is not None

    def test_append_multiple(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        for i in range(5):
            repo.append(
                entity_type="source",
                entity_id="bbc-news",
                metric_name="approval_rate",
                metric_value=0.7 + i * 0.05,
                sample_size=10 + i * 5,
                snapshot_at=now + timedelta(days=i),
            )
        session.commit()

        count = repo.count_for_entity("source", "bbc-news")
        assert count == 5

    def test_append_with_metadata(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        snapshot = repo.append(
            entity_type="source",
            entity_id="bbc-news",
            metric_name="quality_score",
            metric_value=0.9,
            sample_size=30,
            snapshot_at=now,
            metadata={"version": "1.0", "algorithm": "v2"},
        )
        session.commit()

        assert snapshot.metadata["version"] == "1.0"
        assert snapshot.metadata["algorithm"] == "v2"

    def test_append_with_empty_metadata(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        snapshot = repo.append(
            entity_type="source",
            entity_id="bbc-news",
            metric_name="approval_rate",
            metric_value=0.8,
            sample_size=10,
            snapshot_at=now,
        )
        session.commit()

        assert snapshot.metadata == {}


class TestKnowledgeTimelineRepositoryGetTimeline:
    def test_get_timeline_ordered(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        times = [now - timedelta(days=3), now - timedelta(days=1), now - timedelta(days=2)]
        for t in times:
            repo.append(
                entity_type="source",
                entity_id="bbc-news",
                metric_name="approval_rate",
                metric_value=0.8,
                sample_size=10,
                snapshot_at=t,
            )
        session.commit()

        timeline = repo.get_timeline("source", "bbc-news", "approval_rate")
        assert len(timeline) == 3
        # Should be ordered by snapshot_at ASC
        assert timeline[0].snapshot_at < timeline[1].snapshot_at
        assert timeline[1].snapshot_at < timeline[2].snapshot_at

    def test_get_timeline_empty(self, session):
        repo = KnowledgeTimelineRepository(session)
        timeline = repo.get_timeline("source", "nonexistent", "metric")
        assert len(timeline) == 0

    def test_get_timeline_filters_by_metric(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        repo.append("source", "bbc", "approval_rate", 0.8, 10, now)
        repo.append("source", "bbc", "quality_score", 0.9, 10, now)
        repo.append("source", "bbc", "approval_rate", 0.85, 15, now)
        session.commit()

        timeline = repo.get_timeline("source", "bbc", "approval_rate")
        assert len(timeline) == 2

    def test_get_timeline_filters_by_entity(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        repo.append("source", "bbc", "approval_rate", 0.8, 10, now)
        repo.append("source", "cnn", "approval_rate", 0.7, 10, now)
        session.commit()

        timeline = repo.get_timeline("source", "bbc", "approval_rate")
        assert len(timeline) == 1


class TestKnowledgeTimelineRepositoryGetAllForEntity:
    def test_get_all_for_entity(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        repo.append("source", "bbc", "approval_rate", 0.8, 10, now)
        repo.append("source", "bbc", "quality_score", 0.9, 10, now)
        repo.append("source", "cnn", "approval_rate", 0.7, 10, now)
        session.commit()

        results = repo.get_all_for_entity("source", "bbc")
        assert len(results) == 2

    def test_get_all_for_entity_empty(self, session):
        repo = KnowledgeTimelineRepository(session)
        results = repo.get_all_for_entity("source", "nonexistent")
        assert len(results) == 0


class TestKnowledgeTimelineRepositoryCount:
    def test_count_for_entity(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        repo.append("source", "bbc", "m1", 0.8, 10, now)
        repo.append("source", "bbc", "m2", 0.9, 10, now)
        repo.append("source", "cnn", "m1", 0.7, 10, now)
        session.commit()

        assert repo.count_for_entity("source", "bbc") == 2
        assert repo.count_for_entity("source", "cnn") == 1
        assert repo.count_for_entity("source", "nonexistent") == 0


class TestKnowledgeTimelineRepositoryGetLatest:
    def test_get_latest(self, session):
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        repo.append("source", "bbc", "approval_rate", 0.7, 10, now - timedelta(days=5))
        repo.append("source", "bbc", "approval_rate", 0.85, 20, now)
        session.commit()

        latest = repo.get_latest("source", "bbc", "approval_rate")
        assert latest is not None
        assert latest.metric_value == 0.85

    def test_get_latest_nonexistent(self, session):
        repo = KnowledgeTimelineRepository(session)
        latest = repo.get_latest("source", "nonexistent", "metric")
        assert latest is None


class TestKnowledgeTimelineRepositoryAppendOnly:
    """Verify append-only guarantee: no update or delete methods exist."""

    def test_no_update_method(self):
        repo = KnowledgeTimelineRepository.__new__(KnowledgeTimelineRepository)
        assert not hasattr(repo, "update")
        assert not hasattr(repo, "update_snapshot")

    def test_no_delete_method(self):
        repo = KnowledgeTimelineRepository.__new__(KnowledgeTimelineRepository)
        assert not hasattr(repo, "delete")
        assert not hasattr(repo, "delete_snapshot")

    def test_appended_values_are_immutable(self, session):
        """Once a snapshot is appended, its metric_value never changes."""
        repo = KnowledgeTimelineRepository(session)
        now = datetime.now(timezone.utc)
        snap1 = repo.append("source", "bbc", "approval_rate", 0.7, 10, now)
        snap2 = repo.append("source", "bbc", "approval_rate", 0.85, 20, now)
        session.commit()

        timeline = repo.get_timeline("source", "bbc", "approval_rate")
        assert timeline[0].metric_value == 0.7
        assert timeline[1].metric_value == 0.85
        # First snapshot was never modified
