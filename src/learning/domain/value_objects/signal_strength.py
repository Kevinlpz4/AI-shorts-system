"""
SignalStrength Value Object — Encapsulates signal magnitude with decay.

Signal strength represents how impactful a signal is, with an optional
time-based decay factor that reduces strength over time.
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class SignalStrength(ValueObject):
    """Immutable signal strength with optional time decay.

    Attributes:
        value: Signal strength between 0.0 (no impact) and 1.0 (maximum).
        decay_factor: How fast the signal decays over time (0.0-1.0).
            - 0.0 means no decay (signal stays constant).
            - 1.0 means maximum decay (signal disappears immediately).

    Invariants:
        - value MUST be in [0.0, 1.0]
        - decay_factor MUST be in [0.0, 1.0]
    """

    value: float
    decay_factor: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError(
                f"SignalStrength.value must be a number, got {type(self.value).__name__}"
            )
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"SignalStrength.value must be in [0.0, 1.0], got {self.value}"
            )
        if not isinstance(self.decay_factor, (int, float)):
            raise TypeError(
                f"SignalStrength.decay_factor must be a number, got {type(self.decay_factor).__name__}"
            )
        if not (0.0 <= self.decay_factor <= 1.0):
            raise ValueError(
                f"SignalStrength.decay_factor must be in [0.0, 1.0], got {self.decay_factor}"
            )

    def apply_decay(self, elapsed_periods: float) -> SignalStrength:
        """Apply time-based decay and return a new SignalStrength.

        Uses exponential decay: new_value = value * (1 - decay_factor) ^ elapsed

        Args:
            elapsed_periods: Number of time periods elapsed since signal creation.

        Returns:
            A new SignalStrength with the decayed value.
        """
        if elapsed_periods <= 0:
            return self
        factor = (1.0 - self.decay_factor) ** elapsed_periods
        decayed_value = max(0.0, self.value * factor)
        return SignalStrength(value=decayed_value, decay_factor=self.decay_factor)
