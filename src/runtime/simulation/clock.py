"""
Virtual clock — time acceleration for simulation.

Provides a virtual clock that advances time without waiting for real seconds.
All timestamps are generated deterministically from the seed.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone


class VirtualClock:
    """Virtual clock for time-accelerated simulation.

    The clock starts at a fixed point and advances in configurable steps.
    All timestamps are deterministic given the same seed and step sequence.

    Usage::

        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_hours(24)  # +1 day
        now = clock.now()
    """

    def __init__(
        self,
        start_date: str | datetime = "2026-07-01",
        timezone_offset: int = 0,
    ) -> None:
        if isinstance(start_date, str):
            self._current = datetime.strptime(start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        else:
            self._current = start_date

        self._timezone_offset = timezone_offset
        self._total_advanced: float = 0.0
        self._step_count: int = 0
        self._start_wall = time.monotonic()

    @property
    def now(self) -> datetime:
        """Current virtual time."""
        return self._current

    @property
    def total_advanced_hours(self) -> float:
        """Total hours advanced since start."""
        return self._total_advanced

    @property
    def step_count(self) -> int:
        """Number of advance steps taken."""
        return self._step_count

    def advance_hours(self, hours: float) -> datetime:
        """Advance the clock by N hours and return the new time."""
        delta = timedelta(hours=hours)
        self._current += delta
        self._total_advanced += hours
        self._step_count += 1
        return self._current

    def advance_days(self, days: float) -> datetime:
        """Advance the clock by N days and return the new time."""
        return self.advance_hours(days * 24)

    def advance_minutes(self, minutes: float) -> datetime:
        """Advance the clock by N minutes and return the new time."""
        return self.advance_hours(minutes / 60.0)

    def advance_iterations(self, iterations: int, hours_per_iteration: float) -> datetime:
        """Advance by a fixed number of iterations at a given rate."""
        total_hours = iterations * hours_per_iteration
        return self.advance_hours(total_hours)

    def reset(self) -> None:
        """Reset the clock to its initial state."""
        self._current = self._current.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self._total_advanced = 0.0
        self._step_count = 0
        self._start_wall = time.monotonic()

    def elapsed_wall_seconds(self) -> float:
        """Real wall-clock seconds since clock creation."""
        return time.monotonic() - self._start_wall

    def day_of_week(self) -> str:
        """Current day of the week."""
        return self._current.strftime("%A")

    def is_weekend(self) -> bool:
        """Whether the current virtual day is a weekend."""
        return self._current.weekday() >= 5

    def date_str(self) -> str:
        """Current date as YYYY-MM-DD string."""
        return self._current.strftime("%Y-%m-%d")

    def time_str(self) -> str:
        """Current time as HH:MM:SS string."""
        return self._current.strftime("%H:%M:%S")

    def datetime_str(self) -> str:
        """Current datetime as ISO-format string."""
        return self._current.isoformat()

    def __repr__(self) -> str:
        return (
            f"VirtualClock(date={self.date_str()}, "
            f"advanced={self._total_advanced:.1f}h, "
            f"steps={self._step_count})"
        )
