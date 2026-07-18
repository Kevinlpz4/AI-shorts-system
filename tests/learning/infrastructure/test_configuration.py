"""
Tests for Learning Configuration — immutable config dataclass.

Covers:
- LearningConfig default values
- LearningConfig.with_overrides immutability
- Single and multiple field overrides
"""
from __future__ import annotations

import pytest

from learning.infrastructure.configuration import LearningConfig


class TestLearningConfig:
    """Tests for LearningConfig frozen dataclass."""

    def test_default_config(self) -> None:
        """Default config has sensible production values."""
        config = LearningConfig()

        assert config.feature_store_enabled is True
        assert config.signal_decay_factor == 0.1
        assert config.signal_default_window_hours == 24
        assert config.prediction_approve_threshold == 0.7
        assert config.prediction_reject_threshold == 0.3
        assert config.dataset_max_samples == 10000
        assert config.dataset_default_format == "jsonl"
        assert config.knowledge_timeline_enabled is True
        assert config.prediction_cache_ttl == 300
        assert config.analytics_cache_ttl == 600

    def test_with_overrides(self) -> None:
        """with_overrides returns a NEW instance with specified fields changed."""
        original = LearningConfig()
        custom = original.with_overrides(prediction_approve_threshold=0.9)

        # Original unchanged
        assert original.prediction_approve_threshold == 0.7
        # Custom has the override
        assert custom.prediction_approve_threshold == 0.9
        # Other fields preserved
        assert custom.prediction_reject_threshold == 0.3
        assert custom.feature_store_enabled is True

    def test_immutability(self) -> None:
        """LearningConfig is frozen — direct mutation raises."""
        config = LearningConfig()
        with pytest.raises(AttributeError):
            config.feature_store_enabled = False  # type: ignore[misc]

    def test_override_single_field(self) -> None:
        """Override exactly one field, all others stay at defaults."""
        config = LearningConfig()
        custom = config.with_overrides(signal_decay_factor=0.25)

        assert custom.signal_decay_factor == 0.25
        # Verify everything else is default
        assert custom.feature_store_enabled is True
        assert custom.prediction_approve_threshold == 0.7
        assert custom.dataset_max_samples == 10000

    def test_override_multiple_fields(self) -> None:
        """Override several fields simultaneously."""
        config = LearningConfig()
        custom = config.with_overrides(
            signal_decay_factor=0.2,
            prediction_approve_threshold=0.85,
            prediction_reject_threshold=0.15,
            dataset_max_samples=5000,
            prediction_cache_ttl=600,
        )

        assert custom.signal_decay_factor == 0.2
        assert custom.prediction_approve_threshold == 0.85
        assert custom.prediction_reject_threshold == 0.15
        assert custom.dataset_max_samples == 5000
        assert custom.prediction_cache_ttl == 600
        # Unoverridden fields stay at defaults
        assert custom.dataset_default_format == "jsonl"
        assert custom.analytics_cache_ttl == 600
        assert custom.knowledge_timeline_enabled is True

    def test_override_chaining(self) -> None:
        """with_overrides can be chained for incremental customization."""
        base = LearningConfig()
        step1 = base.with_overrides(signal_decay_factor=0.2)
        step2 = step1.with_overrides(prediction_approve_threshold=0.9)

        assert step2.signal_decay_factor == 0.2
        assert step2.prediction_approve_threshold == 0.9
        # Base still default
        assert base.signal_decay_factor == 0.1
        assert base.prediction_approve_threshold == 0.7

    def test_override_preserves_equality(self) -> None:
        """Two configs with same values are equal."""
        a = LearningConfig(prediction_approve_threshold=0.8)
        b = LearningConfig(prediction_approve_threshold=0.8)
        assert a == b

    def test_override_with_invalid_field_raises(self) -> None:
        """Override with a non-existent field raises TypeError."""
        config = LearningConfig()
        with pytest.raises(TypeError):
            config.with_overrides(nonexistent_field=42)  # type: ignore[arg-type]
