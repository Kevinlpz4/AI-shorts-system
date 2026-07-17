"""
TimeWindow Value Object — Encapsulates a time range for signal aggregation.

Used to define the temporal window over which signals are measured.
The start must always be strictly before the end.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class TimeWindow(ValueObject):
    """Immutable time window for signal aggregation.

    Attributes:
        start: Beginning of the window (inclusive).
        end: End of the window (exclusive).

    Invariants:
        - start MUST be strictly before end.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.start, datetime):
            raise TypeError(
                f"TimeWindow.start must be a datetime, got {type(self.start).__name__}"
            )
        if not isinstance(self.end, datetime):
            raise TypeError(
                f"TimeWindow.end must be a datetime, got {type(self.end).__name__}"
            )
        if self.start >= self.end:
            raise ValueError(
                f"TimeWindow.start must be strictly before end, "
                f"got start={self.start}, end={self.end}"
            )

    @property
    def duration(self) -> float:
        """Duration of the window in seconds."""
        return (self.end - self.start).total_seconds()

    def contains(self, dt: datetime) -> bool:
        """Check if a datetime falls within the window [start, end)."""
        return self.start <= dt < self.end

    def overlaps(self, other: TimeWindow) -> bool:
        """Check if this window overlaps with another window."""
        return self.start < other.end and other.start < self.end
