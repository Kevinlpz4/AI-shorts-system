"""
FeatureVector Value Object — Immutable dictionary of extracted article features.

Represents a set of numeric features extracted from an article for scoring
and learning purposes. Uses an immutable mapping to guarantee immutability.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class FeatureVector(ValueObject):
    """Immutable feature vector for article scoring.

    Attributes:
        features: Mapping of feature names to numeric values (float).
            Keys are strings (feature names), values are floats (feature values).

    Invariants:
        - All feature values MUST be numeric (int or float).
        - Feature dict is made immutable on construction (frozen).
    """

    features: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure immutability by converting to a frozen mapping
        if not isinstance(self.features, dict):
            # If already immutable (e.g., MappingProxyType), that's fine
            if not isinstance(self.features, Mapping):
                raise TypeError(
                    f"FeatureVector.features must be a Mapping, got {type(self.features).__name__}"
                )
        # Validate all values are numeric
        for key, value in self.features.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"Feature key must be a string, got {type(key).__name__}"
                )
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Feature '{key}' value must be numeric, got {type(value).__name__}"
                )
        # Make immutable by converting to MappingProxyType
        from types import MappingProxyType

        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))

    def get(self, key: str, default: float = 0.0) -> float:
        """Get a feature value by key, returning default if not found."""
        return self.features.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self.features

    def __len__(self) -> int:
        return len(self.features)

    def keys(self):
        return self.features.keys()

    def values(self):
        return self.features.values()

    def items(self):
        return self.features.items()
