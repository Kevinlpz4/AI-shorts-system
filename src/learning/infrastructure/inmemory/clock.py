"""
Clock Adapters for the Learning Bounded Context.

Provides two clock implementations that satisfy the learning ``ClockPort``:

- ``LearningSystemClock``: Production clock — delegates to
  ``datetime.now(timezone.utc)``.
- ``LearningFrozenClock``: Test clock — frozen time that can be advanced
  or set to a specific datetime.

NOTE: Foundation already provides ``SystemClock`` and ``FrozenClock``.
These adapters are Learning-specific wrappers with a simpler API
(``advance(**kwargs)`` and ``set()``) for ergonomic test usage.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


class LearningSystemClock:
    """Production clock — delegates to datetime.now(timezone.utc).

    Satisfies the learning ``ClockPort`` protocol.
    """

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        return datetime.now(timezone.utc)


class LearningFrozenClock:
    """Test clock — frozen time that can be advanced.

    Satisfies the learning ``ClockPort`` protocol. Time does not advance
    unless explicitly moved via ``advance()`` or ``set()``.

    Args:
        initial: Starting datetime. Defaults to 2026-07-15 UTC.

    Raises:
        ValueError: If ``initial`` is a naive datetime (no timezone).

    Usage::

        clock = LearningFrozenClock()
        assert clock.now() == datetime(2026, 7, 15, tzinfo=timezone.utc)

        clock.advance(hours=2)
        assert clock.now() == datetime(2026, 7, 15, 2, 0, tzinfo=timezone.utc)

        clock.set(datetime(2026, 12, 31, tzinfo=timezone.utc))
        assert clock.now().month == 12
    """

    def __init__(self, initial: datetime | None = None) -> None:
        if initial is None:
            initial = datetime(2026, 7, 15, tzinfo=timezone.utc)
        if initial.tzinfo is None:
            raise ValueError(
                "LearningFrozenClock requires timezone-aware datetime, "
                "got naive"
            )
        self._current = initial

    def now(self) -> datetime:
        """Return the frozen datetime."""
        return self._current

    def advance(self, **kwargs: int | float) -> None:
        """Advance (or rewind) the frozen time.

        Accepts any ``timedelta`` keyword arguments: ``days``,
        ``hours``, ``minutes``, ``seconds``, etc.

        Args:
            **kwargs: Keyword arguments passed to ``timedelta``.

        Usage::

            clock.advance(hours=3)
            clock.advance(days=-1, hours=6)
        """
        self._current += timedelta(**kwargs)

    def set(self, dt: datetime) -> None:
        """Set the frozen time to a specific datetime.

        Args:
            dt: The datetime to set (must be timezone-aware).

        Raises:
            ValueError: If ``dt`` is naive.
        """
        if dt.tzinfo is None:
            raise ValueError(
                "Cannot set to naive datetime, expected timezone-aware"
            )
        self._current = dt
