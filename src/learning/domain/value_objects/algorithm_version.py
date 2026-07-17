"""
AlgorithmVersion Value Object — Immutable semantic version for learning algorithms.

Tracks the version of the learning algorithm that produced a set of weights
or signals, enabling reproducibility and rollback.
"""
from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject


@dataclass(frozen=True)
class AlgorithmVersion(ValueObject):
    """Immutable semantic version for learning algorithms.

    Attributes:
        major: Major version (breaking changes in algorithm).
        minor: Minor version (new features, backward compatible).
        patch: Patch version (bug fixes, backward compatible).

    Invariants:
        - All version components MUST be >= 0.
    """

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            value = getattr(self, name)
            if not isinstance(value, int):
                raise TypeError(
                    f"AlgorithmVersion.{name} must be an int, got {type(value).__name__}"
                )
            if value < 0:
                raise ValueError(
                    f"AlgorithmVersion.{name} must be >= 0, got {value}"
                )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __gt__(self, other: AlgorithmVersion) -> bool:
        return (self.major, self.minor, self.patch) > (
            other.major,
            other.minor,
            other.patch,
        )

    def __ge__(self, other: AlgorithmVersion) -> bool:
        return (self.major, self.minor, self.patch) >= (
            other.major,
            other.minor,
            other.patch,
        )

    def __lt__(self, other: AlgorithmVersion) -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: AlgorithmVersion) -> bool:
        return (self.major, self.minor, self.patch) <= (
            other.major,
            other.minor,
            other.patch,
        )

    def next_major(self) -> AlgorithmVersion:
        """Return a new version with major incremented and minor/patch reset."""
        return AlgorithmVersion(major=self.major + 1, minor=0, patch=0)

    def next_minor(self) -> AlgorithmVersion:
        """Return a new version with minor incremented and patch reset."""
        return AlgorithmVersion(major=self.major, minor=self.minor + 1, patch=0)

    def next_patch(self) -> AlgorithmVersion:
        """Return a new version with patch incremented."""
        return AlgorithmVersion(
            major=self.major, minor=self.minor, patch=self.patch + 1
        )

    @classmethod
    def parse(cls, version_str: str) -> AlgorithmVersion:
        """Parse a version string like '1.2.3' into an AlgorithmVersion.

        Args:
            version_str: A string in the format 'major.minor.patch'.

        Returns:
            AlgorithmVersion instance.

        Raises:
            ValueError: If the format is invalid.
        """
        parts = version_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid version format '{version_str}', expected 'major.minor.patch'"
            )
        try:
            return cls(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid version format '{version_str}': {e}"
            ) from e
