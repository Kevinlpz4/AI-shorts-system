"""Tests for TimeWindow Value Object."""
import pytest
from datetime import datetime, timezone, timedelta
from learning.domain.value_objects.time_window import TimeWindow


class TestTimeWindow:
    def _make_window(self, hours=24):
        now = datetime(2026, 7, 15, tzinfo=timezone.utc)
        return TimeWindow(start=now, end=now + timedelta(hours=hours))

    def test_valid_construction(self):
        w = self._make_window()
        assert w.duration == 24 * 3600

    def test_rejects_start_after_end(self):
        now = datetime(2026, 7, 15, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="strictly before"):
            TimeWindow(start=now, end=now - timedelta(hours=1))

    def test_rejects_start_equals_end(self):
        now = datetime(2026, 7, 15, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="strictly before"):
            TimeWindow(start=now, end=now)

    def test_rejects_non_datetime(self):
        with pytest.raises(TypeError, match="datetime"):
            TimeWindow(start="2026-07-15", end="2026-07-16")  # type: ignore[arg-type]

    def test_contains_inside(self):
        w = self._make_window()
        inside = w.start + timedelta(hours=12)
        assert w.contains(inside)

    def test_contains_at_start(self):
        w = self._make_window()
        assert w.contains(w.start)

    def test_contains_at_end_exclusive(self):
        w = self._make_window()
        assert not w.contains(w.end)

    def test_contains_before(self):
        w = self._make_window()
        assert not w.contains(w.start - timedelta(hours=1))

    def test_overlaps(self):
        w1 = self._make_window(24)
        w2 = TimeWindow(start=w1.start + timedelta(hours=12), end=w1.end + timedelta(hours=12))
        assert w1.overlaps(w2)

    def test_no_overlap(self):
        w1 = self._make_window(24)
        w2 = TimeWindow(start=w1.end + timedelta(hours=1), end=w1.end + timedelta(hours=25))
        assert not w1.overlaps(w2)

    def test_immutable(self):
        w = self._make_window()
        with pytest.raises(AttributeError):
            w.start = datetime.now(timezone.utc)  # type: ignore[misc]

    def test_equality(self):
        now = datetime(2026, 7, 15, tzinfo=timezone.utc)
        a = TimeWindow(start=now, end=now + timedelta(days=1))
        b = TimeWindow(start=now, end=now + timedelta(days=1))
        assert a == b
