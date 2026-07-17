"""Tests for KeywordStat Entity."""
import pytest
from learning.domain.entities.keyword_stat import KeywordStatEntity
from learning.domain.entities.ids import LearningSignalId
from learning.domain.value_objects.keyword_stat_vo import KeywordStat


class TestKeywordStatEntity:
    def test_create_factory(self):
        e = KeywordStatEntity.create(keyword="python", count=10, approved_count=7)
        assert e.keyword == "python"
        assert e.count == 10
        assert e.approved_count == 7

    def test_properties_delegate_to_vo(self):
        ks = KeywordStat(keyword="test", count=5, approved_count=3)
        e = KeywordStatEntity(id=LearningSignalId.generate(), keyword_stat=ks)
        assert e.keyword == "test"
        assert e.count == 5
        assert e.approved_count == 3
        assert e.approval_rate == pytest.approx(0.6)

    def test_has_id(self):
        e = KeywordStatEntity.create(keyword="x", count=1, approved_count=1)
        assert isinstance(e.id, LearningSignalId)

    def test_equality(self):
        id_ = LearningSignalId.generate()
        ks = KeywordStat(keyword="x", count=1, approved_count=1)
        a = KeywordStatEntity(id=id_, keyword_stat=ks)
        b = KeywordStatEntity(id=id_, keyword_stat=ks)
        assert a == b
