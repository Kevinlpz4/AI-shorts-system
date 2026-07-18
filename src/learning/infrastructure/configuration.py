"""
Learning BC Configuration — immutable configuration dataclass.

Provides ``LearningConfig``, a frozen dataclass that holds all
configuration for the Learning BC. Independent of any BC. No globals.

Usage::

    config = LearningConfig()  # defaults
    custom = config.with_overrides(
        prediction_approve_threshold=0.8,
        signal_decay_factor=0.15,
    )
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass


@dataclass(frozen=True)
class LearningConfig:
    """Configuration for the Learning BC.

    Immutable. Use ``with_overrides()`` to create modified copies.

    Attributes:
        feature_store_enabled: Whether the Feature Store is active.
        signal_decay_factor: Rate at which historical signals decay (0.0 - 1.0).
        signal_default_window_hours: Default time window for signal aggregation.
        prediction_approve_threshold: Score above which articles are auto-approved.
        prediction_reject_threshold: Score below which articles are auto-rejected.
        dataset_max_samples: Maximum samples in a generated dataset.
        dataset_default_format: Default export format (jsonl, csv).
        knowledge_timeline_enabled: Whether Knowledge Timeline tracking is active.
        prediction_cache_ttl: TTL in seconds for prediction cache entries.
        analytics_cache_ttl: TTL in seconds for analytics cache entries.
    """

    # Feature Store
    feature_store_enabled: bool = True

    # Signal decay
    signal_decay_factor: float = 0.1
    signal_default_window_hours: int = 24

    # Prediction
    prediction_approve_threshold: float = 0.7
    prediction_reject_threshold: float = 0.3

    # Dataset
    dataset_max_samples: int = 10000
    dataset_default_format: str = "jsonl"

    # Knowledge Timeline
    knowledge_timeline_enabled: bool = True

    # Cache
    prediction_cache_ttl: int = 300
    analytics_cache_ttl: int = 600

    def with_overrides(self, **kwargs) -> LearningConfig:
        """Create a new config with overrides (immutable pattern).

        Returns a NEW LearningConfig instance with the specified fields
        replaced. The original config is never modified.

        Usage::

            config = LearningConfig()
            custom = config.with_overrides(
                prediction_approve_threshold=0.8,
                dataset_max_samples=5000,
            )
        """
        return dataclasses.replace(self, **kwargs)
