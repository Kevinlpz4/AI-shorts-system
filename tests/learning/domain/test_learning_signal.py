"""Tests for LearningSignal Aggregate Root."""
import pytest
from datetime import datetime, timezone, timedelta
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.ids import LearningSignalId
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow


def _make_signal(**overrides):
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    defaults = dict(
        id=LearningSignalId.generate(),
        signal_type=SignalType.KEYWORD,
        dimension="python",
        strength=SignalStrength(value=0.8, decay_factor=0.1),
        sample_size=20,
        approval_rate=0.75,
        window=TimeWindow(start=now - timedelta(days=30), end=now),
    )
    defaults.update(overrides)
    return LearningSignal(**defaults)


class TestLearningSignal:
    def test_valid_construction(self):
        s = _make_signal()
        assert s.signal_type == SignalType.KEYWORD
        assert s.dimension == "python"
        assert s.sample_size == 20

    def test_rejects_negative_sample_size(self):
        with pytest.raises(Exception, match=">= 0"):
            _make_signal(sample_size=-1)

    def test_rejects_approval_rate_above_one(self):
        with pytest.raises(Exception, match="\\[0.0, 1.0\\]"):
            _make_signal(approval_rate=1.5)

    def test_rejects_approval_rate_below_zero(self):
        with pytest.raises(Exception, match="\\[0.0, 1.0\\]"):
            _make_signal(approval_rate=-0.1)

    def test_rejects_empty_dimension(self):
        with pytest.raises(Exception, match="empty"):
            _make_signal(dimension="")

    def test_update_increments_sample_size(self):
        s = _make_signal(sample_size=10, approval_rate=0.5)
        new_window = TimeWindow(
            start=s.window.start - timedelta(days=30),
            end=s.window.end + timedelta(days=30),
        )
        s.update(
            new_sample_size=15,
            new_approval_rate=0.6,
            new_strength=SignalStrength(value=0.6, decay_factor=0.1),
            new_window=new_window,
        )
        assert s.sample_size == 15
        assert s.approval_rate == 0.6

    def test_update_emits_signal_aggregated_event(self):
        s = _make_signal()
        new_window = TimeWindow(
            start=s.window.start - timedelta(days=30),
            end=s.window.end + timedelta(days=30),
        )
        s.update(
            new_sample_size=25,
            new_approval_rate=0.8,
            new_strength=SignalStrength(value=0.8, decay_factor=0.1),
            new_window=new_window,
        )
        events = s.pull_events()
        assert any(e.__class__.__name__ == "SignalAggregated" for e in events)

    def test_update_rejects_invalid_data(self):
        s = _make_signal()
        new_window = TimeWindow(
            start=s.window.start - timedelta(days=30),
            end=s.window.end + timedelta(days=30),
        )
        with pytest.raises(Exception):
            s.update(
                new_sample_size=-1,
                new_approval_rate=0.5,
                new_strength=SignalStrength(value=0.5, decay_factor=0.1),
                new_window=new_window,
            )

    def test_dimension_stripped(self):
        s = _make_signal(dimension="  python  ")
        assert s.dimension == "python"

    def test_last_updated_defaults_to_now(self):
        s = _make_signal()
        assert s.last_updated is not None
