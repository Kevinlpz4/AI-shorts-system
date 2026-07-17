"""
Signal Handler Protocol and Implementations — Open/Closed signal hierarchy.

Each signal type (KEYWORD, SOURCE, CATEGORY, TOPIC, TIME) has its own
handler that knows how to compute signal strength for that dimension.

New signal types are added by implementing a new handler — existing code
is NEVER modified (Open/Closed Principle).

Usage::

    registry = SignalRegistry()
    registry.register(KeywordSignalHandler())
    registry.register(SourceSignalHandler())

    handler = registry.get_handler(SignalType.KEYWORD)
    strength = handler.compute(data)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType


class SignalHandler(Protocol):
    """Protocol defining the interface for signal handlers.

    Each handler knows how to compute signal strength for its dimension.
    Handlers are stateless — they receive data and return a result.
    """

    @property
    def signal_type(self) -> SignalType:
        """The signal type this handler computes."""
        ...

    def compute(self, data: dict) -> SignalStrength:
        """Compute signal strength from the given data.

        Args:
            data: Dictionary containing the data needed to compute
                the signal (e.g., approval counts, sample sizes).

        Returns:
            Computed SignalStrength.
        """
        ...


class _BaseSignalHandler(ABC):
    """Abstract base class providing common behavior for signal handlers.

    Not required by the Protocol, but provides shared utility methods
    for all concrete handlers.
    """

    @staticmethod
    def _compute_from_rates(
        approval_rate: float,
        sample_size: int,
        min_sample: int = 5,
    ) -> SignalStrength:
        """Compute signal strength from approval rate and sample size.

        Uses a simple formula: strength = approval_rate * confidence_factor,
        where confidence_factor increases with sample size.

        Args:
            approval_rate: Rate of approvals (0.0-1.0).
            sample_size: Number of data points.
            min_sample: Minimum sample size for full confidence.

        Returns:
            Computed SignalStrength.
        """
        # Confidence factor: ramps up from 0 to 1 as sample approaches min_sample
        confidence = min(1.0, sample_size / min_sample) if min_sample > 0 else 1.0
        strength_value = approval_rate * confidence
        # Decay is inverse of confidence: less data = faster decay
        decay = max(0.0, 1.0 - confidence) * 0.5
        return SignalStrength(value=strength_value, decay_factor=decay)


class KeywordSignalHandler(_BaseSignalHandler):
    """Computes signal strength for keyword effectiveness.

    Measures how well a specific keyword predicts approval.
    """

    @property
    def signal_type(self) -> SignalType:
        return SignalType.KEYWORD

    def compute(self, data: dict) -> SignalStrength:
        """Compute keyword signal strength.

        Expected data keys:
            - approval_rate (float): Rate of approvals for this keyword.
            - sample_size (int): Number of articles with this keyword.
        """
        approval_rate = float(data.get("approval_rate", 0.0))
        sample_size = int(data.get("sample_size", 0))
        return self._compute_from_rates(approval_rate, sample_size, min_sample=10)


class SourceSignalHandler(_BaseSignalHandler):
    """Computes signal strength for source reliability.

    Measures how reliable a content source is based on approval history.
    """

    @property
    def signal_type(self) -> SignalType:
        return SignalType.SOURCE

    def compute(self, data: dict) -> SignalStrength:
        """Compute source signal strength.

        Expected data keys:
            - approval_rate (float): Rate of approvals for this source.
            - sample_size (int): Number of articles from this source.
        """
        approval_rate = float(data.get("approval_rate", 0.0))
        sample_size = int(data.get("sample_size", 0))
        return self._compute_from_rates(approval_rate, sample_size, min_sample=15)


class CategorySignalHandler(_BaseSignalHandler):
    """Computes signal strength for category performance.

    Measures how well a content category performs across approvals.
    """

    @property
    def signal_type(self) -> SignalType:
        return SignalType.CATEGORY

    def compute(self, data: dict) -> SignalStrength:
        """Compute category signal strength.

        Expected data keys:
            - approval_rate (float): Rate of approvals for this category.
            - sample_size (int): Number of articles in this category.
        """
        approval_rate = float(data.get("approval_rate", 0.0))
        sample_size = int(data.get("sample_size", 0))
        return self._compute_from_rates(approval_rate, sample_size, min_sample=10)


class TopicSignalHandler(_BaseSignalHandler):
    """Computes signal strength for topic engagement.

    Measures audience engagement patterns for a specific topic.
    """

    @property
    def signal_type(self) -> SignalType:
        return SignalType.TOPIC

    def compute(self, data: dict) -> SignalStrength:
        """Compute topic signal strength.

        Expected data keys:
            - approval_rate (float): Rate of approvals for this topic.
            - sample_size (int): Number of articles about this topic.
        """
        approval_rate = float(data.get("approval_rate", 0.0))
        sample_size = int(data.get("sample_size", 0))
        return self._compute_from_rates(approval_rate, sample_size, min_sample=8)


class TimeSignalHandler(_BaseSignalHandler):
    """Computes signal strength for temporal patterns.

    Measures time-based patterns in content approval (e.g., time of day,
    day of week effectiveness).
    """

    @property
    def signal_type(self) -> SignalType:
        return SignalType.TIME

    def compute(self, data: dict) -> SignalStrength:
        """Compute time signal strength.

        Expected data keys:
            - approval_rate (float): Rate of approvals for this time window.
            - sample_size (int): Number of articles in this time window.
        """
        approval_rate = float(data.get("approval_rate", 0.0))
        sample_size = int(data.get("sample_size", 0))
        # Time signals use higher decay since they become less relevant quickly
        strength_value = approval_rate * min(1.0, sample_size / 20)
        decay = 0.3  # Time signals decay moderately fast
        return SignalStrength(value=strength_value, decay_factor=decay)
