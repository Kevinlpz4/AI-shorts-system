"""
Tests for Feature Store — NewsFeatures dataclass and FeatureStore repository.

Covers:
- NewsFeatures construction, defaults, frozen behavior, equality
- FeatureStore upsert (new + update), get, query, count, stats, clear
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.infrastructure.feature_store import FeatureStore, NewsFeatures


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_features(
    *,
    id: str = "f1",
    article_id: str = "a1",
    source_name: str = "reuters",
    title: str = "Test Article",
    source_quality: float = 0.85,
    final_score: float = 0.72,
    editor_decision: str | None = None,
) -> NewsFeatures:
    """Create a NewsFeatures with sensible defaults."""
    return NewsFeatures(
        id=id,
        article_id=article_id,
        source_name=source_name,
        title=title,
        source_quality=source_quality,
        final_score=final_score,
        editor_decision=editor_decision,
    )


# ===========================================================================
# NewsFeatures dataclass
# ===========================================================================


class TestNewsFeatures:
    """Tests for the NewsFeatures frozen dataclass."""

    def test_construction_defaults(self) -> None:
        """Default values are sane — empty strings, 0.0 scores, no decision."""
        nf = NewsFeatures()
        assert nf.id == ""
        assert nf.article_id == ""
        assert nf.source_name == ""
        assert nf.title == ""
        assert nf.source_quality == 0.0
        assert nf.final_score == 0.0
        assert nf.editor_decision is None
        assert nf.metadata == {}

    def test_construction_with_values(self) -> None:
        """All fields can be set at construction time."""
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        nf = NewsFeatures(
            id="f1",
            article_id="a1",
            source_name="reuters",
            title="AI Breakthrough",
            source_quality=0.9,
            keyword_strength=0.8,
            freshness=0.7,
            duplicates=0.1,
            topic_strength=0.85,
            category_strength=0.6,
            historical_success=0.75,
            confidence=0.92,
            final_score=0.81,
            editor_decision="APPROVED",
            created_at=ts,
            metadata={"region": "us"},
        )
        assert nf.id == "f1"
        assert nf.article_id == "a1"
        assert nf.source_name == "reuters"
        assert nf.source_quality == 0.9
        assert nf.confidence == 0.92
        assert nf.editor_decision == "APPROVED"
        assert nf.created_at == ts
        assert nf.metadata == {"region": "us"}

    def test_frozen(self) -> None:
        """NewsFeatures is immutable — mutation raises FrozenInstanceError."""
        nf = NewsFeatures(id="f1")
        with pytest.raises(AttributeError):
            nf.id = "f2"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two NewsFeatures with the same values are equal."""
        ts = datetime(2026, 7, 15, tzinfo=timezone.utc)
        kwargs = dict(
            id="f1",
            article_id="a1",
            source_name="reuters",
            title="Test",
            final_score=0.75,
            created_at=ts,
        )
        a = NewsFeatures(**kwargs)
        b = NewsFeatures(**kwargs)
        assert a == b

    def test_inequality(self) -> None:
        """Two NewsFeatures with different values are not equal."""
        a = NewsFeatures(id="f1", article_id="a1")
        b = NewsFeatures(id="f2", article_id="a2")
        assert a != b


# ===========================================================================
# FeatureStore
# ===========================================================================


class TestFeatureStoreUpsert:
    """Tests for FeatureStore upsert operations."""

    def test_upsert_new(self) -> None:
        """Upsert a new feature record — stored and retrievable."""
        store = FeatureStore()
        nf = _make_features(id="f1", article_id="a1")

        store.upsert(nf)

        assert store.count() == 1
        assert store.get_by_id("f1") is nf

    def test_upsert_update_existing(self) -> None:
        """Upsert with the same article_id replaces the record."""
        store = FeatureStore()
        original = _make_features(id="f1", article_id="a1", final_score=0.5)
        updated = _make_features(id="f2", article_id="a1", final_score=0.9)

        store.upsert(original)
        store.upsert(updated)

        # Should still be 1 record
        assert store.count() == 1
        # Retrieved by article_id should be the updated version
        retrieved = store.get_by_article_id("a1")
        assert retrieved is not None
        assert retrieved.final_score == 0.9
        assert retrieved.id == "f2"


class TestFeatureStoreGet:
    """Tests for FeatureStore retrieval operations."""

    def test_get_by_id(self) -> None:
        """get_by_id returns the correct record."""
        store = FeatureStore()
        nf = _make_features(id="f1")
        store.upsert(nf)

        result = store.get_by_id("f1")
        assert result is nf

    def test_get_by_article_id(self) -> None:
        """get_by_article_id returns the record for the given article."""
        store = FeatureStore()
        nf = _make_features(article_id="a1")
        store.upsert(nf)

        result = store.get_by_article_id("a1")
        assert result is nf

    def test_get_by_article_id_not_found(self) -> None:
        """get_by_article_id returns None for non-existent article."""
        store = FeatureStore()
        assert store.get_by_article_id("nonexistent") is None

    def test_get_by_id_not_found(self) -> None:
        """get_by_id returns None for non-existent ID."""
        store = FeatureStore()
        assert store.get_by_id("nonexistent") is None


class TestFeatureStoreQuery:
    """Tests for FeatureStore query with filters."""

    @pytest.fixture()
    def store(self) -> FeatureStore:
        """Populated FeatureStore for query tests."""
        store = FeatureStore()
        store.upsert(_make_features(id="f1", article_id="a1", source_name="reuters", final_score=0.8, editor_decision="APPROVED"))
        store.upsert(_make_features(id="f2", article_id="a2", source_name="reuters", final_score=0.5, editor_decision="REJECTED"))
        store.upsert(_make_features(id="f3", article_id="a3", source_name="bbc", final_score=0.7, editor_decision="APPROVED"))
        store.upsert(_make_features(id="f4", article_id="a4", source_name="bbc", final_score=0.3, editor_decision=None))
        store.upsert(_make_features(id="f5", article_id="a5", source_name="cnn", final_score=0.9, editor_decision="APPROVED"))
        return store

    def test_query_by_source(self, store: FeatureStore) -> None:
        """Filter by source_name returns only matching records."""
        results = store.query(source_name="reuters")
        assert len(results) == 2
        assert all(f.source_name == "reuters" for f in results)

    def test_query_by_decision(self, store: FeatureStore) -> None:
        """Filter by decision returns only matching records."""
        results = store.query(decision="APPROVED")
        assert len(results) == 3
        assert all(f.editor_decision == "APPROVED" for f in results)

    def test_query_by_min_score(self, store: FeatureStore) -> None:
        """Filter by min_score (inclusive) returns records >= threshold."""
        results = store.query(min_score=0.7)
        assert len(results) == 3
        assert all(f.final_score >= 0.7 for f in results)

    def test_query_by_max_score(self, store: FeatureStore) -> None:
        """Filter by max_score (inclusive) returns records <= threshold."""
        results = store.query(max_score=0.5)
        assert len(results) == 2
        assert all(f.final_score <= 0.5 for f in results)

    def test_query_combined_filters(self, store: FeatureStore) -> None:
        """Multiple filters compose with AND semantics."""
        results = store.query(source_name="reuters", decision="APPROVED")
        assert len(results) == 1
        assert results[0].id == "f1"

    def test_query_with_limit(self, store: FeatureStore) -> None:
        """Limit caps the number of results returned."""
        results = store.query(limit=2)
        assert len(results) == 2

    def test_query_no_filters_returns_all(self, store: FeatureStore) -> None:
        """Query with no filters returns all records."""
        results = store.query()
        assert len(results) == 5


class TestFeatureStoreCount:
    """Tests for FeatureStore counting and stats."""

    def test_count(self) -> None:
        """count returns the total number of feature records."""
        store = FeatureStore()
        assert store.count() == 0

        store.upsert(_make_features(id="f1", article_id="a1"))
        assert store.count() == 1

        store.upsert(_make_features(id="f2", article_id="a2"))
        assert store.count() == 2

    def test_count_by_decision(self) -> None:
        """count_by_decision groups records by editor_decision."""
        store = FeatureStore()
        store.upsert(_make_features(id="f1", article_id="a1", editor_decision="APPROVED"))
        store.upsert(_make_features(id="f2", article_id="a2", editor_decision="APPROVED"))
        store.upsert(_make_features(id="f3", article_id="a3", editor_decision="REJECTED"))
        store.upsert(_make_features(id="f4", article_id="a4", editor_decision=None))

        counts = store.count_by_decision()
        assert counts == {"APPROVED": 2, "REJECTED": 1, "PENDING": 1}

    def test_stats_by_source(self) -> None:
        """stats_by_source returns aggregated statistics for a source."""
        store = FeatureStore()
        store.upsert(_make_features(id="f1", article_id="a1", source_name="reuters", final_score=0.6, editor_decision="APPROVED"))
        store.upsert(_make_features(id="f2", article_id="a2", source_name="reuters", final_score=0.8, editor_decision="REJECTED"))
        store.upsert(_make_features(id="f3", article_id="a3", source_name="reuters", final_score=0.7, editor_decision=None))

        stats = store.stats_by_source("reuters")
        assert stats["count"] == 3
        assert stats["avg_score"] == pytest.approx(0.7)
        assert stats["min_score"] == 0.6
        assert stats["max_score"] == 0.8
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
        assert stats["pending"] == 1

    def test_stats_by_source_empty(self) -> None:
        """stats_by_source returns count=0 for non-existent source."""
        store = FeatureStore()
        stats = store.stats_by_source("nonexistent")
        assert stats == {"count": 0}


class TestFeatureStoreClear:
    """Tests for FeatureStore clear operation."""

    def test_clear(self) -> None:
        """clear removes all feature records."""
        store = FeatureStore()
        store.upsert(_make_features(id="f1", article_id="a1"))
        store.upsert(_make_features(id="f2", article_id="a2"))
        assert store.count() == 2

        store.clear()
        assert store.count() == 0
        assert store.get_by_id("f1") is None
        assert store.get_by_article_id("a1") is None
