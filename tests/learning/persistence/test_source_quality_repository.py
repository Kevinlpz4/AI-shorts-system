"""
Tests for SourceQualityRepository — save, upsert, find, exists.
"""
from __future__ import annotations

import pytest

from learning.domain.entities.ids import SourceQualityId
from learning.domain.exceptions.errors import LearningErrorCode
from learning.persistence.repositories.source_quality_repository import SourceQualityRepository
from foundation.result.result import Success, Failure


class TestSourceQualityRepositorySave:
    def test_save_and_find_by_id(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality()
        repo.save(profile)
        session.commit()

        result = repo.find_by_id(profile.id)
        assert isinstance(result, Success)
        assert result.unwrap().id == profile.id

    def test_upsert_insert(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality(source_name="new-source")
        repo.save(profile)
        session.commit()

        assert repo.exists_by_source_name("new-source")

    def test_upsert_update(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality(source_name="my-source")
        repo.save(profile)
        session.flush()

        # Record a new decision
        profile.record_decision("approved")
        repo.save(profile)
        session.commit()

        result = repo.find_by_source_name("my-source")
        loaded = result.unwrap()
        assert loaded.total_decisions == 11
        assert loaded.approved_count == 9

    def test_save_preserves_keywords(self, session, make_source_quality):
        from learning.domain.value_objects.keyword_stat_vo import KeywordStat

        repo = SourceQualityRepository(session)
        keywords = {"python": KeywordStat(keyword="python", count=5, approved_count=4)}
        profile = make_source_quality(keywords=keywords)
        repo.save(profile)
        session.commit()

        result = repo.find_by_id(profile.id)
        loaded = result.unwrap()
        assert "python" in loaded.keywords
        assert loaded.keywords["python"].count == 5


class TestSourceQualityRepositoryFindById:
    def test_find_existing(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality()
        repo.save(profile)
        session.commit()

        result = repo.find_by_id(profile.id)
        assert isinstance(result, Success)

    def test_find_nonexistent(self, session):
        repo = SourceQualityRepository(session)
        result = repo.find_by_id(SourceQualityId.generate())
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.SOURCE_QUALITY_NOT_FOUND


class TestSourceQualityRepositoryFindBySourceName:
    def test_find_by_source_name(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality(source_name="bbc-news")
        repo.save(profile)
        session.commit()

        result = repo.find_by_source_name("bbc-news")
        assert isinstance(result, Success)
        assert result.unwrap().source_name == "bbc-news"

    def test_find_nonexistent_source(self, session):
        repo = SourceQualityRepository(session)
        result = repo.find_by_source_name("nonexistent")
        assert isinstance(result, Failure)


class TestSourceQualityRepositoryExists:
    def test_exists_true(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        profile = make_source_quality(source_name="existing")
        repo.save(profile)
        session.commit()

        assert repo.exists_by_source_name("existing") is True

    def test_exists_false(self, session):
        repo = SourceQualityRepository(session)
        assert repo.exists_by_source_name("nonexistent") is False


class TestSourceQualityRepositoryFindAllActive:
    def test_find_active(self, session, make_source_quality):
        repo = SourceQualityRepository(session)
        active = make_source_quality(source_name="active", total_decisions=5, approved_count=3, rejected_count=2)
        inactive = make_source_quality(source_name="inactive", total_decisions=0, approved_count=0, rejected_count=0)
        repo.save(active)
        repo.save(inactive)
        session.commit()

        results = repo.find_all_active()
        assert len(results) == 1
        assert results[0].source_name == "active"

    def test_find_active_empty(self, session):
        repo = SourceQualityRepository(session)
        results = repo.find_all_active()
        assert len(results) == 0
