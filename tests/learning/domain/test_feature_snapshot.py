"""Tests for FeatureSnapshot Value Object."""
import pytest
from datetime import datetime, timezone
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot


class TestFeatureSnapshot:
    def _make_snapshot(self, **overrides):
        defaults = dict(
            base_score=0.7,
            freshness_score=0.8,
            keyword_bonus=0.1,
            source_bonus=0.2,
            topic_penalty=0.05,
            confidence=0.9,
            final_score=0.75,
            timestamp=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        defaults.update(overrides)
        return FeatureSnapshot(**defaults)

    def test_valid_construction(self):
        s = self._make_snapshot()
        assert s.base_score == 0.7
        assert s.final_score == 0.75

    def test_rejects_score_out_of_range(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            self._make_snapshot(base_score=1.5)

    def test_rejects_non_numeric_score(self):
        with pytest.raises(TypeError, match="number"):
            self._make_snapshot(base_score="high")  # type: ignore[arg-type]

    def test_rejects_non_datetime_timestamp(self):
        with pytest.raises(TypeError, match="datetime"):
            self._make_snapshot(timestamp="2026-07-15")  # type: ignore[arg-type]

    def test_as_dict(self):
        s = self._make_snapshot()
        d = s.as_dict()
        assert d["base_score"] == 0.7
        assert isinstance(d["timestamp"], datetime)

    def test_immutable(self):
        s = self._make_snapshot()
        with pytest.raises(AttributeError):
            s.base_score = 0.5  # type: ignore[misc]

    def test_equality(self):
        a = self._make_snapshot()
        b = self._make_snapshot()
        assert a == b

    def test_historical_reproducibility(self):
        """FeatureSnapshot captures enough data to reproduce a decision."""
        s = self._make_snapshot(
            base_score=0.6,
            freshness_score=0.9,
            keyword_bonus=0.15,
            source_bonus=0.3,
            topic_penalty=0.1,
            confidence=0.85,
            final_score=0.72,
        )
        # Given the same snapshot, a decision should be reproducible
        assert s.base_score + s.keyword_bonus + s.source_bonus - s.topic_penalty == pytest.approx(0.95, abs=0.01)
        assert s.confidence >= 0.8
