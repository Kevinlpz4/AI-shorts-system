"""Tests for Confidence Value Object."""
import pytest
from learning.domain.value_objects.confidence import Confidence


class TestConfidence:
    def test_valid_construction(self):
        c = Confidence(value=0.8, sample_size=50)
        assert c.value == 0.8
        assert c.sample_size == 50

    def test_boundary_values(self):
        assert Confidence(value=0.0, sample_size=0)
        assert Confidence(value=1.0, sample_size=999)

    def test_rejects_value_above_one(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            Confidence(value=1.5, sample_size=10)

    def test_rejects_value_below_zero(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            Confidence(value=-0.1, sample_size=10)

    def test_rejects_negative_sample_size(self):
        with pytest.raises(ValueError, match=">= 0"):
            Confidence(value=0.5, sample_size=-1)

    def test_rejects_non_numeric_value(self):
        with pytest.raises(TypeError, match="number"):
            Confidence(value="high", sample_size=10)  # type: ignore[arg-type]

    def test_rejects_non_int_sample_size(self):
        with pytest.raises(TypeError, match="int"):
            Confidence(value=0.5, sample_size=10.5)  # type: ignore[arg-type]

    def test_is_high(self):
        assert Confidence(value=0.8, sample_size=10).is_high
        assert Confidence(value=0.9, sample_size=10).is_high
        assert not Confidence(value=0.79, sample_size=10).is_high
        assert not Confidence(value=0.0, sample_size=10).is_high

    def test_is_reliable(self):
        assert Confidence(value=0.8, sample_size=30).is_reliable
        assert Confidence(value=1.0, sample_size=100).is_reliable
        assert not Confidence(value=0.8, sample_size=29).is_reliable
        assert not Confidence(value=0.7, sample_size=50).is_reliable

    def test_immutable(self):
        c = Confidence(value=0.5, sample_size=10)
        with pytest.raises(AttributeError):
            c.value = 0.9  # type: ignore[misc]

    def test_equality(self):
        a = Confidence(value=0.8, sample_size=50)
        b = Confidence(value=0.8, sample_size=50)
        assert a == b

    def test_inequality(self):
        a = Confidence(value=0.8, sample_size=50)
        b = Confidence(value=0.9, sample_size=50)
        assert a != b
