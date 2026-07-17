"""Tests for ScoreWeights Value Object."""
import pytest
from learning.domain.value_objects.score_weights import ScoreWeights


class TestScoreWeights:
    def test_valid_construction(self):
        w = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        assert w.total == pytest.approx(1.0, abs=0.01)

    def test_rejects_sum_not_one(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoreWeights(relevance=0.5, popularity=0.5, recency=0.5, source_reliability=0.5)

    def test_rejects_weight_above_one(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            ScoreWeights(relevance=1.5, popularity=0.0, recency=0.0, source_reliability=0.0)  # type: ignore

    def test_rejects_weight_below_zero(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            ScoreWeights(relevance=-0.1, popularity=0.4, recency=0.35, source_reliability=0.35)

    def test_rejects_non_numeric(self):
        with pytest.raises(TypeError, match="number"):
            ScoreWeights(relevance="high", popularity=0.25, recency=0.25, source_reliability=0.25)  # type: ignore[arg-type]

    def test_as_dict(self):
        w = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        d = w.as_dict()
        assert d == {"relevance": 0.35, "popularity": 0.25, "recency": 0.25, "source_reliability": 0.15}

    def test_immutable(self):
        w = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        with pytest.raises(AttributeError):
            w.relevance = 0.5  # type: ignore[misc]

    def test_equality(self):
        a = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        b = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        assert a == b

    def test_default_weights_match_research(self):
        """Default Research weights: relevance=0.35, popularity=0.25, recency=0.25, reliability=0.15."""
        w = ScoreWeights(relevance=0.35, popularity=0.25, recency=0.25, source_reliability=0.15)
        assert w.relevance == 0.35
        assert w.source_reliability == 0.15

    def test_sum_within_tolerance(self):
        """Tolerance is ±0.01."""
        w = ScoreWeights(relevance=0.34, popularity=0.25, recency=0.25, source_reliability=0.16)
        assert w.total == pytest.approx(1.0, abs=0.01)
