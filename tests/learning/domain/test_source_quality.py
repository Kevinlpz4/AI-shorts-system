"""Tests for SourceQualityProfile Aggregate Root."""
import pytest
from datetime import datetime, timezone
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.entities.ids import SourceQualityId


def _make_profile(**overrides):
    defaults = dict(
        id=SourceQualityId.generate(),
        source_name="reddit",
        total_decisions=0,
        approved_count=0,
        rejected_count=0,
        auto_approved_count=0,
        auto_rejected_count=0,
        overridden_count=0,
    )
    defaults.update(overrides)
    return SourceQualityProfile(**defaults)


class TestSourceQualityProfile:
    def test_valid_construction(self):
        p = _make_profile()
        assert p.source_name == "reddit"
        assert p.total_decisions == 0
        assert p.approval_rate == 0.0

    def test_with_counts(self):
        p = _make_profile(
            total_decisions=10,
            approved_count=7,
            rejected_count=3,
        )
        assert p.approval_rate == pytest.approx(0.7)

    def test_rejects_negative_counts(self):
        with pytest.raises(Exception, match=">= 0"):
            _make_profile(approved_count=-1)

    def test_rejects_total_mismatch(self):
        with pytest.raises(Exception, match="must equal sum"):
            _make_profile(total_decisions=10, approved_count=5, rejected_count=2)

    def test_rejects_empty_source_name(self):
        with pytest.raises(Exception, match="empty"):
            _make_profile(source_name="")

    def test_record_approved(self):
        p = _make_profile()
        p.record_decision("approved")
        assert p.approved_count == 1
        assert p.total_decisions == 1
        assert p.approval_rate == 1.0

    def test_record_rejected(self):
        p = _make_profile()
        p.record_decision("rejected")
        assert p.rejected_count == 1
        assert p.total_decisions == 1
        assert p.approval_rate == 0.0

    def test_record_auto_approved(self):
        p = _make_profile()
        p.record_decision("auto_approved")
        assert p.auto_approved_count == 1
        assert p.total_decisions == 1

    def test_record_auto_rejected(self):
        p = _make_profile()
        p.record_decision("auto_rejected")
        assert p.auto_rejected_count == 1

    def test_record_overridden(self):
        p = _make_profile()
        p.record_decision("overridden")
        assert p.overridden_count == 1

    def test_record_invalid_type(self):
        p = _make_profile()
        with pytest.raises(Exception, match="Invalid decision_type"):
            p.record_decision("invalid")

    def test_record_with_keywords(self):
        p = _make_profile()
        p.record_decision("approved", keywords=["python", "fastapi"])
        assert "python" in p.keywords
        assert p.keywords["python"].count == 1
        assert p.keywords["python"].approved_count == 1

    def test_record_rejected_keyword(self):
        p = _make_profile()
        p.record_decision("rejected", keywords=["clickbait"])
        assert p.keywords["clickbait"].approved_count == 0

    def test_multiple_keyword_updates(self):
        p = _make_profile()
        p.record_decision("approved", keywords=["python"])
        p.record_decision("approved", keywords=["python"])
        p.record_decision("rejected", keywords=["python"])
        assert p.keywords["python"].count == 3
        assert p.keywords["python"].approved_count == 2

    def test_approval_rate_recomputes(self):
        p = _make_profile()
        p.record_decision("approved")
        p.record_decision("rejected")
        assert p.approval_rate == pytest.approx(0.5)
        p.record_decision("approved")
        assert p.approval_rate == pytest.approx(2 / 3)

    def test_source_name_stripped(self):
        p = _make_profile(source_name="  reddit  ")
        assert p.source_name == "reddit"
