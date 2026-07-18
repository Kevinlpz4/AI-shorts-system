"""
Tests for FeatureStoreRepository — upsert, query filters, stats.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.persistence.mappers.news_features_mapper import _NewsFeatures
from learning.persistence.repositories.feature_store_repository import FeatureStoreRepository


def _make_features(
    article_id: str = "article-1",
    source_name: str = "bbc-news",
    title: str = "Test Article",
    final_score: float = 0.75,
    editor_decision: str | None = None,
) -> _NewsFeatures:
    return _NewsFeatures(
        article_id=article_id,
        source_name=source_name,
        title=title,
        source_quality=0.8,
        keyword_strength=0.6,
        freshness=0.9,
        duplicates=0.1,
        topic_strength=0.7,
        category_strength=0.5,
        historical_success=0.6,
        confidence=0.85,
        final_score=final_score,
        editor_decision=editor_decision,
        created_at=datetime.now(timezone.utc),
    )


class TestFeatureStoreRepositoryUpsert:
    def test_upsert_insert(self, session):
        repo = FeatureStoreRepository(session)
        features = _make_features()
        result = repo.upsert(features)
        session.commit()

        assert result.article_id == "article-1"
        assert result.final_score == 0.75

    def test_upsert_update(self, session):
        repo = FeatureStoreRepository(session)
        f1 = _make_features(final_score=0.5)
        repo.upsert(f1)
        session.flush()

        f2 = _make_features(final_score=0.9)
        result = repo.upsert(f2)
        session.commit()

        assert result.final_score == 0.9

    def test_upsert_preserves_id(self, session):
        repo = FeatureStoreRepository(session)
        f1 = _make_features(article_id="art-42")
        repo.upsert(f1)
        session.commit()

        found = repo.find_by_article_id("art-42")
        assert found is not None
        assert found.article_id == "art-42"


class TestFeatureStoreRepositoryFindByArticleId:
    def test_find_existing(self, session):
        repo = FeatureStoreRepository(session)
        features = _make_features(article_id="find-me")
        repo.upsert(features)
        session.commit()

        found = repo.find_by_article_id("find-me")
        assert found is not None
        assert found.article_id == "find-me"

    def test_find_nonexistent(self, session):
        repo = FeatureStoreRepository(session)
        found = repo.find_by_article_id("nonexistent")
        assert found is None


class TestFeatureStoreRepositoryQuery:
    def test_query_by_source(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="a1", source_name="bbc"))
        repo.upsert(_make_features(article_id="a2", source_name="bbc"))
        repo.upsert(_make_features(article_id="a3", source_name="cnn"))
        session.commit()

        results = repo.query(source_name="bbc")
        assert len(results) == 2

    def test_query_by_decision(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="a1", editor_decision="APPROVED"))
        repo.upsert(_make_features(article_id="a2", editor_decision="REJECTED"))
        repo.upsert(_make_features(article_id="a3", editor_decision="APPROVED"))
        session.commit()

        results = repo.query(editor_decision="APPROVED")
        assert len(results) == 2

    def test_query_by_score_range(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="a1", final_score=0.3))
        repo.upsert(_make_features(article_id="a2", final_score=0.7))
        repo.upsert(_make_features(article_id="a3", final_score=0.9))
        session.commit()

        results = repo.query(min_score=0.5, max_score=0.8)
        assert len(results) == 1
        assert results[0].article_id == "a2"

    def test_query_combined_filters(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(
            article_id="a1", source_name="bbc", editor_decision="APPROVED", final_score=0.8
        ))
        repo.upsert(_make_features(
            article_id="a2", source_name="bbc", editor_decision="REJECTED", final_score=0.8
        ))
        repo.upsert(_make_features(
            article_id="a3", source_name="cnn", editor_decision="APPROVED", final_score=0.8
        ))
        session.commit()

        results = repo.query(source_name="bbc", editor_decision="APPROVED")
        assert len(results) == 1
        assert results[0].article_id == "a1"

    def test_query_empty(self, session):
        repo = FeatureStoreRepository(session)
        results = repo.query()
        assert len(results) == 0

    def test_query_limit(self, session):
        repo = FeatureStoreRepository(session)
        for i in range(10):
            repo.upsert(_make_features(article_id=f"a{i}"))
        session.commit()

        results = repo.query(limit=3)
        assert len(results) == 3


class TestFeatureStoreRepositoryStats:
    def test_count_by_decision(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="a1", editor_decision="APPROVED"))
        repo.upsert(_make_features(article_id="a2", editor_decision="APPROVED"))
        repo.upsert(_make_features(article_id="a3", editor_decision="REJECTED"))
        session.commit()

        assert repo.count_by_decision("APPROVED") == 2
        assert repo.count_by_decision("REJECTED") == 1
        assert repo.count_by_decision("NONEXISTENT") == 0

    def test_count_all(self, session):
        repo = FeatureStoreRepository(session)
        assert repo.count_all() == 0
        repo.upsert(_make_features(article_id="a1"))
        repo.upsert(_make_features(article_id="a2"))
        session.commit()
        assert repo.count_all() == 2

    def test_get_average_score(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="a1", final_score=0.6))
        repo.upsert(_make_features(article_id="a2", final_score=0.8))
        session.commit()

        avg = repo.get_average_score()
        assert abs(avg - 0.7) < 0.001

    def test_get_average_score_empty(self, session):
        repo = FeatureStoreRepository(session)
        assert repo.get_average_score() == 0.0


class TestFeatureStoreRepositoryDelete:
    def test_delete_existing(self, session):
        repo = FeatureStoreRepository(session)
        repo.upsert(_make_features(article_id="to-delete"))
        session.commit()

        deleted = repo.delete_by_article_id("to-delete")
        session.commit()
        assert deleted is True
        assert repo.find_by_article_id("to-delete") is None

    def test_delete_nonexistent(self, session):
        repo = FeatureStoreRepository(session)
        deleted = repo.delete_by_article_id("nonexistent")
        assert deleted is False
