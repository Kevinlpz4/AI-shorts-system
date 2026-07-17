"""
LearningSignal — Aggregate Root for learning signal tracking.

Uses COMPOSITION for signal types: the signal hierarchy is handled
via SignalHandler implementations (see signals/handlers.py), not via
inheritance. This follows the Open/Closed Principle — new signal types
are added by implementing a new handler, NOT by modifying this class.

Invariants:
  - I-01: sample_size MUST be >= 0
  - I-02: approval_rate MUST be in [0.0, 1.0]
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from foundation.base.aggregate_root import AggregateRoot

from learning.domain.entities.ids import LearningSignalId
from learning.domain.events.learning_events import SignalAggregated
from learning.domain.exceptions import LearningDomainError
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow


@dataclass(eq=False, init=False)
class LearningSignal(AggregateRoot):
    """Aggregate root for a learning signal.

    A signal represents an aggregated insight derived from multiple
    feedback records, measured along a specific dimension (keyword,
    source, category, topic, or time).

    The signal hierarchy (KeywordSignalHandler, SourceSignalHandler, etc.)
    is handled via COMPOSITION, not inheritance. Each handler knows how
    to compute signal strength for its dimension.

    Attributes:
        id: Unique identity.
        signal_type: The dimension this signal measures (KEYWORD, SOURCE, etc.).
        dimension: The specific value within the dimension (e.g., keyword text).
        strength: Computed signal strength with decay.
        sample_size: Number of feedback records contributing to this signal.
        approval_rate: Rate of approvals among contributing records (0.0-1.0).
        window: Time window over which this signal was computed.
        last_updated: When this signal was last updated.
    """

    id: LearningSignalId
    signal_type: SignalType
    dimension: str
    strength: SignalStrength
    sample_size: int
    approval_rate: float
    window: TimeWindow
    last_updated: datetime

    def __init__(
        self,
        id: LearningSignalId,
        signal_type: SignalType,
        dimension: str,
        strength: SignalStrength,
        sample_size: int,
        approval_rate: float,
        window: TimeWindow,
        last_updated: datetime | None = None,
    ) -> None:
        """Initialize a LearningSignal.

        Args:
            id: Unique identity.
            signal_type: Dimension of the signal.
            dimension: Specific value within the dimension.
            strength: Signal strength with decay.
            sample_size: Number of contributing records.
            approval_rate: Approval rate (0.0-1.0).
            window: Time window of aggregation.
            last_updated: Last update timestamp (default: now UTC).

        Raises:
            LearningDomainError: If invariants are violated.
        """
        from datetime import datetime, timezone

        # I-01: sample_size >= 0
        if sample_size < 0:
            raise LearningDomainError(
                f"LearningSignal.sample_size must be >= 0, got {sample_size} (I-01)"
            )

        # I-02: approval_rate in [0.0, 1.0]
        if not (0.0 <= approval_rate <= 1.0):
            raise LearningDomainError(
                f"LearningSignal.approval_rate must be in [0.0, 1.0], "
                f"got {approval_rate} (I-02)"
            )

        # Validate dimension not empty
        if not dimension or not dimension.strip():
            raise LearningDomainError(
                "LearningSignal.dimension must not be empty"
            )

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "signal_type", signal_type)
        object.__setattr__(self, "dimension", dimension.strip())
        object.__setattr__(self, "strength", strength)
        object.__setattr__(self, "sample_size", sample_size)
        object.__setattr__(self, "approval_rate", approval_rate)
        object.__setattr__(self, "window", window)
        object.__setattr__(
            self,
            "last_updated",
            last_updated or datetime.now(timezone.utc),
        )
        # Initialize AggregateRoot._events
        object.__setattr__(self, "_events", [])

    def update(
        self,
        new_sample_size: int,
        new_approval_rate: float,
        new_strength: SignalStrength,
        new_window: TimeWindow,
    ) -> None:
        """Update the signal with new aggregated data.

        Args:
            new_sample_size: New sample size.
            new_approval_rate: New approval rate.
            new_strength: New signal strength.
            new_window: New time window.

        Raises:
            LearningDomainError: If invariants are violated.
        """
        from datetime import datetime, timezone

        if new_sample_size < 0:
            raise LearningDomainError(
                f"sample_size must be >= 0, got {new_sample_size}"
            )
        if not (0.0 <= new_approval_rate <= 1.0):
            raise LearningDomainError(
                f"approval_rate must be in [0.0, 1.0], got {new_approval_rate}"
            )

        object.__setattr__(self, "sample_size", new_sample_size)
        object.__setattr__(self, "approval_rate", new_approval_rate)
        object.__setattr__(self, "strength", new_strength)
        object.__setattr__(self, "window", new_window)
        object.__setattr__(self, "last_updated", datetime.now(timezone.utc))

        self.register_event(
            SignalAggregated(
                signal_id=self.id,
                signal_type=self.signal_type.value,
                dimension=self.dimension,
                strength_value=self.strength.value,
                window=self.window,
            )
        )
