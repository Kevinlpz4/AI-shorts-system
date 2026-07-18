"""
In-memory repository implementations for the Learning Bounded Context.

All repositories use ``dict[str, Entity]`` as their storage, keyed by
``str(entity.id)``. They implement the corresponding repository Protocols
defined in ``learning.domain.ports.repositories``.

These implementations are:
    - Deterministic: no external dependencies.
    - Not thread-safe: no locking or atomic operations.
    - Volatile: data is lost when the process exits.
    - LSP-compliant: they behave identically to future persistent
      implementations in terms of exceptions and guarantees.
"""
from __future__ import annotations

from datetime import datetime

from foundation.result.result import Error, Result

from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
)
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType


class InMemoryFeedbackRepository:
    """In-memory store for ``FeedbackRecord`` aggregate roots (immutable).

    Stores feedback in a ``dict[str, FeedbackRecord]`` keyed by
    ``str(feedback.id)``.

    LSP: ``save()`` raises ``ValueError`` for duplicates since
    FeedbackRecord is immutable (there is no "update" operation).
    """

    def __init__(self) -> None:
        self._store: dict[str, FeedbackRecord] = {}

    def save(self, feedback: FeedbackRecord) -> None:
        """Persist a FeedbackRecord (always creation, never update).

        Raises:
            ValueError: If a FeedbackRecord with the same ID already exists.
        """
        key = str(feedback.id)
        if key in self._store:
            raise ValueError(
                f"Duplicate feedback: {key}"
            )
        self._store[key] = feedback

    def find_by_id(self, id: FeedbackId) -> Result[FeedbackRecord]:
        """Find a FeedbackRecord by its unique identity."""
        key = str(id)
        if key not in self._store:
            return Result.failure(
                Error(
                    code=LearningErrorCode.FEEDBACK_NOT_FOUND,
                    message=f"Feedback {id} not found",
                )
            )
        return Result.success(self._store[key])

    def find_by_topic_id(self, topic_id: str) -> list[FeedbackRecord]:
        """Return all FeedbackRecords for a topic."""
        return [f for f in self._store.values() if f.topic_id == topic_id]

    def find_by_source(self, source_name: str) -> list[FeedbackRecord]:
        """Return all FeedbackRecords from a source."""
        return [f for f in self._store.values() if f.source_name == source_name]

    def find_all_in_window(
        self, start: datetime, end: datetime
    ) -> list[FeedbackRecord]:
        """Return all FeedbackRecords within a time range.

        Inclusive on start, exclusive on end (``start <= captured_at < end``).
        """
        return [
            f for f in self._store.values()
            if start <= f.captured_at < end
        ]

    def count_by_decision(self, decision: DecisionType) -> int:
        """Count FeedbackRecords with a given decision type."""
        return sum(
            1 for f in self._store.values()
            if f.decision == decision
        )


class InMemoryLearningSignalRepository:
    """In-memory store for ``LearningSignal`` aggregate roots.

    Stores signals in a ``dict[str, LearningSignal]`` keyed by
    ``str(signal.id)``.

    LSP: ``save()`` is an upsert — replaces if same ID exists.
    ``save_batch()`` is also upsert-based.
    """

    def __init__(self) -> None:
        self._store: dict[str, LearningSignal] = {}

    def save(self, signal: LearningSignal) -> None:
        """Persist a LearningSignal (upsert — replaces if same ID)."""
        self._store[str(signal.id)] = signal

    def save_batch(self, signals: list[LearningSignal]) -> None:
        """Persist multiple LearningSignals (upsert each)."""
        for s in signals:
            self._store[str(s.id)] = s

    def find_by_id(self, id: LearningSignalId) -> Result[LearningSignal]:
        """Find a LearningSignal by its unique identity."""
        key = str(id)
        if key not in self._store:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SIGNAL_NOT_FOUND,
                    message=f"Signal {id} not found",
                )
            )
        return Result.success(self._store[key])

    def find_by_type_and_dimension(
        self, signal_type: SignalType, dimension: str
    ) -> Result[LearningSignal]:
        """Find a LearningSignal by its type and dimension."""
        for s in self._store.values():
            if s.signal_type == signal_type and s.dimension == dimension:
                return Result.success(s)
        return Result.failure(
            Error(
                code=LearningErrorCode.SIGNAL_NOT_FOUND,
                message=(
                    f"Signal type={signal_type.value} "
                    f"dimension={dimension} not found"
                ),
            )
        )

    def find_by_window(
        self, start: datetime, end: datetime
    ) -> list[LearningSignal]:
        """Return signals whose time window overlaps with [start, end)."""
        return [
            s for s in self._store.values()
            if s.window.start < end and s.window.end > start
        ]

    def find_all_active(self) -> list[LearningSignal]:
        """Return all signals with sample_size > 0."""
        return [s for s in self._store.values() if s.sample_size > 0]


class InMemorySourceQualityRepository:
    """In-memory store for ``SourceQualityProfile`` aggregate roots.

    Stores profiles in a ``dict[str, SourceQualityProfile]`` keyed by
    ``str(profile.id)``.
    """

    def __init__(self) -> None:
        self._store: dict[str, SourceQualityProfile] = {}

    def save(self, profile: SourceQualityProfile) -> None:
        """Persist a SourceQualityProfile (upsert)."""
        self._store[str(profile.id)] = profile

    def find_by_id(self, id: SourceQualityId) -> Result[SourceQualityProfile]:
        """Find a SourceQualityProfile by its unique identity."""
        key = str(id)
        if key not in self._store:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SOURCE_QUALITY_NOT_FOUND,
                    message=f"SourceQuality {id} not found",
                )
            )
        return Result.success(self._store[key])

    def find_by_source_name(
        self, source_name: str
    ) -> Result[SourceQualityProfile]:
        """Find a SourceQualityProfile by source name."""
        for p in self._store.values():
            if p.source_name == source_name:
                return Result.success(p)
        return Result.failure(
            Error(
                code=LearningErrorCode.SOURCE_QUALITY_NOT_FOUND,
                message=f"Source '{source_name}' not found",
            )
        )

    def find_all_active(self) -> list[SourceQualityProfile]:
        """Return all profiles with total_decisions > 0."""
        return [p for p in self._store.values() if p.total_decisions > 0]

    def exists_by_source_name(self, source_name: str) -> bool:
        """Verify if a profile exists for the given source name."""
        return any(
            p.source_name == source_name for p in self._store.values()
        )


class InMemoryLearningModelRepository:
    """In-memory store for ``LearningModel`` aggregate roots.

    Stores models in a ``dict[str, LearningModel]`` keyed by
    ``str(model.id)``.
    """

    def __init__(self) -> None:
        self._store: dict[str, LearningModel] = {}

    def save(self, model: LearningModel) -> None:
        """Persist a LearningModel (upsert)."""
        self._store[str(model.id)] = model

    def find_by_id(self, id: LearningModelId) -> Result[LearningModel]:
        """Find a LearningModel by its unique identity."""
        key = str(id)
        if key not in self._store:
            return Result.failure(
                Error(
                    code=LearningErrorCode.MODEL_NOT_FOUND,
                    message=f"Model {id} not found",
                )
            )
        return Result.success(self._store[key])

    def find_current(self) -> Result[LearningModel]:
        """Find the current LearningModel (highest algorithm version)."""
        if not self._store:
            return Result.failure(
                Error(
                    code=LearningErrorCode.MODEL_NOT_FOUND,
                    message="No models found",
                )
            )
        latest = max(
            self._store.values(),
            key=lambda m: (
                m.algorithm_version.major,
                m.algorithm_version.minor,
                m.algorithm_version.patch,
            ),
        )
        return Result.success(latest)

    def find_by_version(
        self, version_str: str
    ) -> Result[LearningModel]:
        """Find a LearningModel by version string (e.g., '1.2.3')."""
        target = AlgorithmVersion.parse(version_str)
        for m in self._store.values():
            if m.algorithm_version == target:
                return Result.success(m)
        return Result.failure(
            Error(
                code=LearningErrorCode.MODEL_NOT_FOUND,
                message=f"Model v{version_str} not found",
            )
        )
