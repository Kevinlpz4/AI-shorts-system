"""
LearningModelRepository — SQLAlchemy implementation of LearningModelRepository Protocol.

find_current() returns the model with the highest algorithm version.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from foundation.result.result import Error, Result
from learning.domain.entities.ids import LearningModelId
from learning.domain.entities.learning_model import LearningModel
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.ports.repositories import LearningModelRepository as LearningModelRepositoryProtocol
from learning.persistence.mappers.learning_model_mapper import LearningModelMapper
from learning.persistence.models.learning_model import LearningModelModel


class LearningModelRepository(LearningModelRepositoryProtocol):
    """SQLAlchemy implementation for LearningModel persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, model: LearningModel) -> None:
        """Persist a LearningModel (upsert by id)."""
        existing = (
            self._session.query(LearningModelModel)
            .filter(LearningModelModel.id == str(model.id))
            .first()
        )
        if existing is not None:
            db_model = LearningModelMapper.to_model(model, version=existing.version + 1)
            existing.algorithm_version_str = db_model.algorithm_version_str
            existing.weights_json = db_model.weights_json
            existing.minimum_confidence = db_model.minimum_confidence
            existing.minimum_sample_size = db_model.minimum_sample_size
            existing.active_rules_json = db_model.active_rules_json
            existing.updated_at = db_model.updated_at
            existing.version = db_model.version
        else:
            db_model = LearningModelMapper.to_model(model)
            self._session.add(db_model)
        self._session.flush()

    def find_by_id(self, id: LearningModelId) -> Result[LearningModel]:
        """Find a LearningModel by its identity."""
        model = (
            self._session.query(LearningModelModel)
            .filter(LearningModelModel.id == str(id))
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.MODEL_NOT_FOUND,
                    message=f"LearningModel not found: {id}",
                )
            )
        return Result.success(LearningModelMapper.to_domain(model))

    def find_current(self) -> Result[LearningModel]:
        """Find the LearningModel with the highest algorithm version.

        Uses tuple comparison on parsed version components.
        """
        all_models = self._session.query(LearningModelModel).all()
        if not all_models:
            return Result.failure(
                Error(
                    code=LearningErrorCode.MODEL_NOT_FOUND,
                    message="No LearningModel found",
                )
            )
        # Sort by parsed version (major, minor, patch) descending
        best = max(
            all_models,
            key=lambda m: tuple(int(x) for x in m.algorithm_version_str.split(".")),
        )
        return Result.success(LearningModelMapper.to_domain(best))

    def find_by_version(self, version_str: str) -> Result[LearningModel]:
        """Find a LearningModel by its version string (e.g., '1.2.3')."""
        model = (
            self._session.query(LearningModelModel)
            .filter(LearningModelModel.algorithm_version_str == version_str)
            .first()
        )
        if model is None:
            return Result.failure(
                Error(
                    code=LearningErrorCode.MODEL_NOT_FOUND,
                    message=f"LearningModel not found for version: {version_str}",
                )
            )
        return Result.success(LearningModelMapper.to_domain(model))
