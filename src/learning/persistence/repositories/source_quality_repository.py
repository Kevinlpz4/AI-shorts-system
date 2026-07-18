"""
SourceQualityRepository — SQLAlchemy implementation of SourceQualityRepository Protocol.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from foundation.result.result import Error, Result
from learning.domain.entities.ids import SourceQualityId
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.ports.repositories import SourceQualityRepository as SourceQualityRepositoryProtocol
from learning.persistence.mappers.source_quality_mapper import SourceQualityMapper
from learning.persistence.models.source_quality import SourceQualityProfileModel


class SourceQualityRepository(SourceQualityRepositoryProtocol):
    """SQLAlchemy implementation for SourceQualityProfile persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, profile: SourceQualityProfile) -> None:
        """Persist a SourceQualityProfile (upsert by source_name)."""
        existing = (
            self._session.query(SourceQualityProfileModel)
            .filter(SourceQualityProfileModel.source_name == profile.source_name)
            .first()
        )
        if existing is not None:
            # Update version for optimistic locking
            model = SourceQualityMapper.to_model(profile, version=existing.version + 1)
            existing.total_decisions = model.total_decisions
            existing.approved_count = model.approved_count
            existing.rejected_count = model.rejected_count
            existing.auto_approved_count = model.auto_approved_count
            existing.auto_rejected_count = model.auto_rejected_count
            existing.overridden_count = model.overridden_count
            existing.approval_rate = model.approval_rate
            existing.keywords_json = model.keywords_json
            existing.last_updated = model.last_updated
            existing.version = model.version
        else:
            model = SourceQualityMapper.to_model(profile)
            self._session.add(model)
        self._session.flush()

    def find_by_id(self, id: SourceQualityId) -> Result[SourceQualityProfile]:
        """Find a SourceQualityProfile by its identity."""
        model = (
            self._session.query(SourceQualityProfileModel)
            .filter(SourceQualityProfileModel.id == str(id))
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SOURCE_QUALITY_NOT_FOUND,
                    message=f"SourceQualityProfile not found: {id}",
                )
            )
        return Result.success(SourceQualityMapper.to_domain(model))

    def find_by_source_name(
        self, source_name: str
    ) -> Result[SourceQualityProfile]:
        """Find a SourceQualityProfile by source name."""
        model = (
            self._session.query(SourceQualityProfileModel)
            .filter(SourceQualityProfileModel.source_name == source_name)
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.SOURCE_QUALITY_NOT_FOUND,
                    message=f"SourceQualityProfile not found for source: {source_name}",
                )
            )
        return Result.success(SourceQualityMapper.to_domain(model))

    def find_all_active(self) -> list[SourceQualityProfile]:
        """Return all profiles with total_decisions > 0."""
        models = (
            self._session.query(SourceQualityProfileModel)
            .filter(SourceQualityProfileModel.total_decisions > 0)
            .all()
        )
        return [SourceQualityMapper.to_domain(m) for m in models]

    def exists_by_source_name(self, source_name: str) -> bool:
        """Check if a profile exists for the given source name."""
        count = (
            self._session.query(SourceQualityProfileModel)
            .filter(SourceQualityProfileModel.source_name == source_name)
            .count()
        )
        return count > 0
