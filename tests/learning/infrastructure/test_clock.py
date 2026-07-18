"""
Tests for Learning Clock adapters.

Covers LearningSystemClock and LearningFrozenClock.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.infrastructure.inmemory.clock import (
    LearningFrozenClock,
    LearningSystemClock,
)


class TestLearningSystemClock:
    """Tests for the production clock adapter."""

    def test_system_clock_returns_datetime(self) -> None:
        clock = LearningSystemClock()
        result = clock.now()

        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        # Should be very close to current UTC time
        now = datetime.now(timezone.utc)
        diff = abs((result - now).total_seconds())
        assert diff < 1.0


class TestLearningFrozenClock:
    """Tests for the test clock adapter."""

    def test_frozen_clock_initial_time(self) -> None:
        clock = LearningFrozenClock()

        assert clock.now() == datetime(2026, 7, 15, tzinfo=timezone.utc)

    def test_frozen_clock_custom_initial(self) -> None:
        custom = datetime(2025, 1, 1, tzinfo=timezone.utc)
        clock = LearningFrozenClock(initial=custom)

        assert clock.now() == custom

    def test_frozen_clock_advance(self) -> None:
        clock = LearningFrozenClock()

        clock.advance(hours=3)

        assert clock.now() == datetime(2026, 7, 15, 3, 0, tzinfo=timezone.utc)

    def test_frozen_clock_advance_days(self) -> None:
        clock = LearningFrozenClock()

        clock.advance(days=5)

        assert clock.now() == datetime(2026, 7, 20, tzinfo=timezone.utc)

    def test_frozen_clock_set(self) -> None:
        clock = LearningFrozenClock()
        target = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        clock.set(target)

        assert clock.now() == target

    def test_frozen_clock_naive_initial_raises(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            LearningFrozenClock(initial=datetime(2026, 7, 15))

    def test_frozen_clock_set_naive_raises(self) -> None:
        clock = LearningFrozenClock()
        with pytest.raises(ValueError, match="timezone-aware"):
            clock.set(datetime(2026, 12, 31))
