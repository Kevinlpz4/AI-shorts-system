"""
FeedbackRepository — SQLAlchemy implementation of FeedbackRepository Protocol.

FeedbackRecord is IMMUTABLE: save() only inserts, never updates.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from foundation.result.result import Error, Result
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import FeedbackId
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.ports.repositories import FeedbackRepository as FeedbackRepositoryProtocol
from learning.domain.value_objects.decision_type import DecisionType
from learning.persistence.mappers.feedback_mapper import FeedbackRecordMapper
from learning.persistence.models.feedback import FeedbackRecordModel


class FeedbackRepository(FeedbackRepositoryProtocol):
    """SQLAlchemy implementation for FeedbackRecord persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, feedback: FeedbackRecord) -> None:
        """Persist a FeedbackRecord (insert only — immutable).

        Raises:
            ValueError: If a FeedbackRecord with the same ID already exists.
        """
        existing = (
            self._session.query(FeedbackRecordModel)
            .filter(FeedbackRecordModel.id == str(feedback.id))
            .first()
        )
        if existing is not None:
            raise ValueError(
                f"FeedbackRecord with id {feedback.id} already exists "
                f"(feedback is immutable — cannot update)"
            )
        model = FeedbackRecordMapper.to_model(feedback)
        self._session.add(model)
        self._session.flush()

    def find_by_id(self, id: FeedbackId) -> Result[FeedbackRecord]:
        """Find a FeedbackRecord by its identity."""
        model = (
            self._session.query(FeedbackRecordModel)
            .filter(FeedbackRecordModel.id == str(id))
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.FEEDBACK_NOT_FOUND,
                    message=f"FeedbackRecord not found: {id}",
                )
            )
        return Result.success(FeedbackRecordMapper.to_domain(model))

    def find_by_topic_id(self, topic_id: str) -> list[FeedbackRecord]:
        """Return all FeedbackRecords for a given topic."""
        models = (
            self._session.query(FeedbackRecordModel)
            .filter(FeedbackRecordModel.topic_id == topic_id)
            .order_by(FeedbackRecordModel.captured_at.desc())
            .all()
        )
        return [FeedbackRecordMapper.to_domain(m) for m in models]

    def find_by_source(self, source_name: str) -> list[FeedbackRecord]:
        """Return all FeedbackRecords from a given source."""
        models = (
            self._session.query(FeedbackRecordModel)
            .filter(FeedbackRecordModel.source_name == source_name)
            .order_by(FeedbackRecordModel.captured_at.desc())
            .all()
        )
        return [FeedbackRecordMapper.to_domain(m) for m in models]

    def find_all_in_window(
        self, start: datetime, end: datetime
    ) -> list[FeedbackRecord]:
        """Return all FeedbackRecords within a time range."""
        models = (
            self._session.query(FeedbackRecordModel)
            .filter(
                FeedbackRecordModel.captured_at >= start,
                FeedbackRecordModel.captured_at < end,
            )
            .order_by(FeedbackRecordModel.captured_at.asc())
            .all()
        )
        return [FeedbackRecordMapper.to_domain(m) for m in models]

    def count_by_decision(self, decision: DecisionType) -> int:
        """Count FeedbackRecords with a specific decision type."""
        count = (
            self._session.query(func.count(FeedbackRecordModel.id))
            .filter(FeedbackRecordModel.decision == decision.value)
            .scalar()
        )
        return count or 0
