"""Tests for SignalStrength Value Object."""
import pytest
from learning.domain.value_objects.signal_strength import SignalStrength


class TestSignalStrength:
    def test_valid_construction(self):
        s = SignalStrength(value=0.8, decay_factor=0.1)
        assert s.value == 0.8
        assert s.decay_factor == 0.1

    def test_rejects_value_out_of_range(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            SignalStrength(value=1.5, decay_factor=0.1)

    def test_rejects_decay_out_of_range(self):
        with pytest.raises(ValueError, match="\\[0.0, 1.0\\]"):
            SignalStrength(value=0.5, decay_factor=1.5)

    def test_rejects_non_numeric(self):
        with pytest.raises(TypeError, match="number"):
            SignalStrength(value="high", decay_factor=0.1)  # type: ignore[arg-type]

    def test_apply_decay_no_periods(self):
        s = SignalStrength(value=0.8, decay_factor=0.1)
        result = s.apply_decay(0)
        assert result == s

    def test_apply_decay_negative_periods(self):
        s = SignalStrength(value=0.8, decay_factor=0.1)
        result = s.apply_decay(-1)
        assert result == s

    def test_apply_decay_reduces_value(self):
        s = SignalStrength(value=0.8, decay_factor=0.5)
        result = s.apply_decay(1)
        assert result.value < 0.8
        assert result.value == pytest.approx(0.4, abs=0.01)

    def test_apply_decay_preserves_decay_factor(self):
        s = SignalStrength(value=0.8, decay_factor=0.3)
        result = s.apply_decay(5)
        assert result.decay_factor == 0.3

    def test_apply_decay_never_goes_below_zero(self):
        s = SignalStrength(value=0.1, decay_factor=0.9)
        result = s.apply_decay(100)
        assert result.value >= 0.0

    def test_apply_decay_no_decay(self):
        s = SignalStrength(value=0.8, decay_factor=0.0)
        result = s.apply_decay(10)
        assert result.value == 0.8

    def test_immutable(self):
        s = SignalStrength(value=0.8, decay_factor=0.1)
        with pytest.raises(AttributeError):
            s.value = 0.5  # type: ignore[misc]

    def test_equality(self):
        a = SignalStrength(value=0.8, decay_factor=0.1)
        b = SignalStrength(value=0.8, decay_factor=0.1)
        assert a == b
