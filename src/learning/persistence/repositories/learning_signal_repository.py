"""
LearningSignalRepository — SQLAlchemy implementation of LearningSignalRepository Protocol.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from foundation.result.result import Error, Result
from learning.domain.entities.ids import LearningSignalId
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.ports.repositories import LearningSignalRepository as LearningSignalRepositoryProtocol
from learning.domain.value_objects.signal_type import SignalType
from learning.persistence.mappers.learning_signal_mapper import LearningSignalMapper
from learning.persistence.models.learning_signal import LearningSignalModel


class LearningSignalRepository(LearningSignalRepositoryProtocol):
    """SQLAlchemy implementation for LearningSignal persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, signal: LearningSignal) -> None:
        """Persist a LearningSignal (upsert: insert or update)."""
        existing = (
            self._session.query(LearningSignalModel)
            .filter(LearningSignalModel.id == str(signal.id))
            .first()
        )
        if existing is not None:
            # Update version for optimistic locking
            model = LearningSignalMapper.to_model(signal, version=existing.version + 1)
            existing.signal_type = model.signal_type
            existing.dimension = model.dimension
            existing.strength_json = model.strength_json
            existing.sample_size = model.sample_size
            existing.approval_rate = model.approval_rate
            existing.window_json = model.window_json
            existing.last_updated = model.last_updated
            existing.version = model.version
        else:
            model = LearningSignalMapper.to_model(signal)
            self._session.add(model)
        self._session.flush()

    def save_batch(self, signals: list[LearningSignal]) -> None:
        """Persist multiple LearningSignals in a single operation."""
        for signal in signals:
            self.save(signal)
        self._session.flush()

    def find_by_id(self, id: LearningSignalId) -> Result[LearningSignal]:
        """Find a LearningSignal by its identity."""
        model = (
            self._session.query(LearningSignalModel)
            .filter(LearningSignalModel.id == str(id))
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SIGNAL_NOT_FOUND,
                    message=f"LearningSignal not found: {id}",
                )
            )
        return Result.success(LearningSignalMapper.to_domain(model))

    def find_by_type_and_dimension(
        self, signal_type: SignalType, dimension: str
    ) -> Result[LearningSignal]:
        """Find a LearningSignal by its type and dimension."""
        model = (
            self._session.query(LearningSignalModel)
            .filter(
                LearningSignalModel.signal_type == signal_type.value,
                LearningSignalModel.dimension == dimension,
            )
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SIGNAL_NOT_FOUND,
                    message=f"LearningSignal not found for type={signal_type.value}, dimension={dimension}",
                )
            )
        return Result.success(LearningSignalMapper.to_domain(model))

    def find_by_window(
        self, start: datetime, end: datetime
    ) -> list[LearningSignal]:
        """Return all signals within a time range."""
        models = (
            self._session.query(LearningSignalModel)
            .filter(
                LearningSignalModel.last_updated >= start,
                LearningSignalModel.last_updated < end,
            )
            .order_by(LearningSignalModel.last_updated.asc())
            .all()
        )
        return [LearningSignalMapper.to_domain(m) for m in models]

    def find_all_active(self) -> list[LearningSignal]:
        """Return all signals with sample_size > 0."""
        models = (
            self._session.query(LearningSignalModel)
            .filter(LearningSignalModel.sample_size > 0)
            .all()
        )
        return [LearningSignalMapper.to_domain(m) for m in models]
