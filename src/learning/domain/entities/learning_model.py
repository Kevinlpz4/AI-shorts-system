"""
LearningModel — Aggregate Root representing learning algorithm state.

Holds the current weights, version, configuration, and active rules
for the learning algorithm. Does NOT perform calculations — that
responsibility lives in the Application Layer.

Invariants:
  - I-01: minimum_confidence MUST be in [0.0, 1.0]
  - I-02: minimum_sample_size MUST be >= 1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from foundation.base.aggregate_root import AggregateRoot

from learning.domain.entities.ids import LearningModelId
from learning.domain.events.learning_events import ScoreAdjusted, LearningModelUpdated
from learning.domain.exceptions import LearningDomainError
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights


@dataclass(eq=False, init=False)
class LearningModel(AggregateRoot):
    """Aggregate root for learning algorithm state.

    Manages the current configuration of the learning algorithm:
    scoring weights, confidence thresholds, active rules, and versioning.
    State transitions emit domain events for auditing and rollback.

    Attributes:
        id: Unique identity.
        algorithm_version: Current version of the learning algorithm.
        current_weights: Current scoring weight configuration.
        minimum_confidence: Minimum confidence threshold (0.0-1.0).
        minimum_sample_size: Minimum sample size for valid signals (>= 1).
        active_rules: List of active learning rule names.
        created_at: When this model was first created.
        updated_at: When this model was last updated.
    """

    id: LearningModelId
    algorithm_version: AlgorithmVersion
    current_weights: ScoreWeights
    minimum_confidence: float
    minimum_sample_size: int
    active_rules: list[str]
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        id: LearningModelId,
        algorithm_version: AlgorithmVersion,
        current_weights: ScoreWeights,
        minimum_confidence: float = 0.5,
        minimum_sample_size: int = 10,
        active_rules: list[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """Initialize a LearningModel.

        Args:
            id: Unique identity.
            algorithm_version: Version of the algorithm.
            current_weights: Scoring weight configuration.
            minimum_confidence: Confidence threshold (default: 0.5).
            minimum_sample_size: Minimum sample size (default: 10).
            active_rules: Active rule names (default: empty list).
            created_at: Creation timestamp (default: now UTC).
            updated_at: Last update timestamp (default: now UTC).

        Raises:
            LearningDomainError: If invariants are violated.
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # I-01: minimum_confidence in [0.0, 1.0]
        if not (0.0 <= minimum_confidence <= 1.0):
            raise LearningDomainError(
                f"LearningModel.minimum_confidence must be in [0.0, 1.0], "
                f"got {minimum_confidence} (I-01)"
            )

        # I-02: minimum_sample_size >= 1
        if minimum_sample_size < 1:
            raise LearningDomainError(
                f"LearningModel.minimum_sample_size must be >= 1, "
                f"got {minimum_sample_size} (I-02)"
            )

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "algorithm_version", algorithm_version)
        object.__setattr__(self, "current_weights", current_weights)
        object.__setattr__(self, "minimum_confidence", minimum_confidence)
        object.__setattr__(self, "minimum_sample_size", minimum_sample_size)
        object.__setattr__(self, "active_rules", list(active_rules or []))
        object.__setattr__(self, "created_at", created_at or now)
        object.__setattr__(self, "updated_at", updated_at or now)
        # Initialize AggregateRoot._events
        object.__setattr__(self, "_events", [])

    def adjust_weights(
        self,
        new_weights: ScoreWeights,
        reason: str,
    ) -> None:
        """Adjust scoring weights and emit ScoreAdjusted event.

        Args:
            new_weights: New weight configuration.
            reason: Human-readable reason for the adjustment.

        Raises:
            LearningDomainError: If reason is empty.
        """
        from datetime import datetime, timezone

        if not reason or not reason.strip():
            raise LearningDomainError(
                "adjust_weights requires a non-empty reason"
            )

        old_weights = self.current_weights
        object.__setattr__(self, "current_weights", new_weights)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self.register_event(
            ScoreAdjusted(
                model_id=self.id,
                old_weights=old_weights,
                new_weights=new_weights,
                reason=reason.strip(),
                adjusted_at=self.updated_at,
            )
        )

    def update_version(self, new_version: AlgorithmVersion) -> None:
        """Update the algorithm version and emit LearningModelUpdated event.

        Args:
            new_version: New algorithm version.

        Raises:
            LearningDomainError: If new_version is not greater than current.
        """
        from datetime import datetime, timezone

        if not (new_version > self.algorithm_version):
            raise LearningDomainError(
                f"New version {new_version} must be greater than "
                f"current version {self.algorithm_version}"
            )

        old_version = str(self.algorithm_version)
        object.__setattr__(self, "algorithm_version", new_version)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

        self.register_event(
            LearningModelUpdated(
                model_id=self.id,
                old_version=old_version,
                new_version=str(new_version),
                updated_at=self.updated_at,
            )
        )

    def add_rule(self, rule_name: str) -> None:
        """Add an active learning rule.

        Args:
            rule_name: Name of the rule to activate.
        """
        from datetime import datetime, timezone

        if not rule_name or not rule_name.strip():
            raise LearningDomainError("rule_name must not be empty")

        if rule_name.strip() in self.active_rules:
            return  # Idempotent — already active

        new_rules = list(self.active_rules) + [rule_name.strip()]
        object.__setattr__(self, "active_rules", new_rules)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))

    def remove_rule(self, rule_name: str) -> None:
        """Remove a learning rule from active rules.

        Args:
            rule_name: Name of the rule to deactivate.
        """
        from datetime import datetime, timezone

        if rule_name.strip() not in self.active_rules:
            return  # Idempotent — not active

        new_rules = [r for r in self.active_rules if r != rule_name.strip()]
        object.__setattr__(self, "active_rules", new_rules)
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))
