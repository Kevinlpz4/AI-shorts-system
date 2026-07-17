"""Tests for KeywordStat Value Object."""
import pytest
from learning.domain.value_objects.keyword_stat_vo import KeywordStat


class TestKeywordStat:
    def test_valid_construction(self):
        ks = KeywordStat(keyword="python", count=10, approved_count=7)
        assert ks.keyword == "python"
        assert ks.count == 10
        assert ks.approved_count == 7

    def test_approval_rate(self):
        ks = KeywordStat(keyword="python", count=10, approved_count=7)
        assert ks.approval_rate == pytest.approx(0.7)

    def test_approval_rate_zero_count(self):
        ks = KeywordStat(keyword="python", count=0, approved_count=0)
        assert ks.approval_rate == 0.0

    def test_is_effective(self):
        assert KeywordStat(keyword="x", count=5, approved_count=4).is_effective  # 0.8 >= 0.7
        assert not KeywordStat(keyword="x", count=4, approved_count=4).is_effective  # count < 5
        assert not KeywordStat(keyword="x", count=10, approved_count=3).is_effective  # rate < 0.7

    def test_rejects_empty_keyword(self):
        with pytest.raises(ValueError, match="empty"):
            KeywordStat(keyword="", count=1, approved_count=1)

    def test_rejects_negative_count(self):
        with pytest.raises(ValueError, match=">= 0"):
            KeywordStat(keyword="x", count=-1, approved_count=0)

    def test_rejects_approved_exceeds_count(self):
        with pytest.raises(ValueError, match="must be <= count"):
            KeywordStat(keyword="x", count=5, approved_count=10)

    def test_immutable(self):
        ks = KeywordStat(keyword="x", count=1, approved_count=1)
        with pytest.raises(AttributeError):
            ks.keyword = "y"  # type: ignore[misc]

    def test_equality(self):
        a = KeywordStat(keyword="x", count=5, approved_count=3)
        b = KeywordStat(keyword="x", count=5, approved_count=3)
        assert a == b
