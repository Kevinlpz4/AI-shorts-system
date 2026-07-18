"""
Scenario 7: Feature Store Consistency

Validates FeatureStore upsert, query, and count semantics.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.feature_store import FeatureStore, NewsFeatures


class TestFeatureStoreConsistency:
    """Verify FeatureStore maintains one record per article."""

    def test_upsert_and_query(self):
        """Upsert creates a record, query retrieves it."""
        store = FeatureStore()

        features = NewsFeatures(
            id="f1",
            article_id="article-1",
            source_name="reuters",
            source_quality=0.85,
            final_score=0.72,
            editor_decision="APPROVED",
        )
        store.upsert(features)

        result = store.get_by_article_id("article-1")
        assert result is not None
        assert result.source_quality == 0.85
        assert result.final_score == 0.72

    def test_upsert_updates_existing(self):
        """Upsert on existing article replaces the record."""
        store = FeatureStore()

        # First insert
        features_v1 = NewsFeatures(
            id="f1",
            article_id="article-1",
            source_name="reuters",
            source_quality=0.85,
            final_score=0.72,
            editor_decision="APPROVED",
        )
        store.upsert(features_v1)

        # Update
        features_v2 = NewsFeatures(
            id="f1",
            article_id="article-1",
            source_name="reuters",
            source_quality=0.90,
            final_score=0.80,
            editor_decision="APPROVED",
        )
        store.upsert(features_v2)

        result = store.get_by_article_id("article-1")
        assert result.source_quality == 0.90
        assert store.count() == 1  # Still one record per article

    def test_count(self):
        """Count returns correct number of records."""
        store = FeatureStore()
        assert store.count() == 0

        store.upsert(NewsFeatures(id="f1", article_id="a1"))
        store.upsert(NewsFeatures(id="f2", article_id="a2"))
        assert store.count() == 2

    def test_query_by_source(self):
        """Query filters by source_name."""
        store = FeatureStore()
        store.upsert(NewsFeatures(id="f1", article_id="a1", source_name="reuters"))
        store.upsert(NewsFeatures(id="f2", article_id="a2", source_name="bbc"))
        store.upsert(NewsFeatures(id="f3", article_id="a3", source_name="reuters"))

        results = store.query(source_name="reuters")
        assert len(results) == 2

    def test_query_by_decision(self):
        """Query filters by editor_decision (non-None)."""
        store = FeatureStore()
        store.upsert(NewsFeatures(
            id="f1", article_id="a1", editor_decision="APPROVED"
        ))
        store.upsert(NewsFeatures(
            id="f2", article_id="a2", editor_decision="REJECTED"
        ))
        store.upsert(NewsFeatures(
            id="f3", article_id="a3", editor_decision=None
        ))

        approved = store.query(decision="APPROVED")
        assert len(approved) == 1
        rejected = store.query(decision="REJECTED")
        assert len(rejected) == 1

        # NOTE: query(decision=None) means "don't filter by decision"
        # (because `if decision:` is falsy for None), so it returns all records
        all_records = store.query(decision=None)
        assert len(all_records) == 3

    def test_count_by_decision(self):
        """count_by_decision groups correctly."""
        store = FeatureStore()
        store.upsert(NewsFeatures(id="f1", article_id="a1", editor_decision="APPROVED"))
        store.upsert(NewsFeatures(id="f2", article_id="a2", editor_decision="APPROVED"))
        store.upsert(NewsFeatures(id="f3", article_id="a3", editor_decision="REJECTED"))

        counts = store.count_by_decision()
        assert counts["APPROVED"] == 2
        assert counts["REJECTED"] == 1

    def test_stats_by_source(self):
        """stats_by_source computes aggregate statistics."""
        store = FeatureStore()
        store.upsert(NewsFeatures(
            id="f1", article_id="a1", source_name="reuters",
            final_score=0.8, editor_decision="APPROVED",
        ))
        store.upsert(NewsFeatures(
            id="f2", article_id="a2", source_name="reuters",
            final_score=0.6, editor_decision="REJECTED",
        ))

        stats = store.stats_by_source("reuters")
        assert stats["count"] == 2
        assert stats["avg_score"] == pytest.approx(0.7)
        assert stats["approved"] == 1
        assert stats["rejected"] == 1

    def test_get_by_id(self):
        """get_by_id returns the correct record."""
        store = FeatureStore()
        store.upsert(NewsFeatures(id="f1", article_id="a1", source_name="reuters"))

        result = store.get_by_id("f1")
        assert result is not None
        assert result.article_id == "a1"

        missing = store.get_by_id("nonexistent")
        assert missing is None

    def test_clear(self):
        """clear removes all records."""
        store = FeatureStore()
        store.upsert(NewsFeatures(id="f1", article_id="a1"))
        store.upsert(NewsFeatures(id="f2", article_id="a2"))
        assert store.count() == 2

        store.clear()
        assert store.count() == 0
