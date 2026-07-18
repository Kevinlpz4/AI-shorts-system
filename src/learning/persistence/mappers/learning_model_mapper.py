"""
LearningModelMapper — Domain <-> SQLAlchemy model mapping for LearningModel.

LearningModel uses object.__setattr__ internally.
The mapper reconstructs via __init__ with all fields.
"""
from __future__ import annotations

import json

from learning.domain.entities.ids import LearningModelId
from learning.domain.entities.learning_model import LearningModel
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.persistence.models.learning_model import LearningModelModel


class LearningModelMapper:
    """Maps LearningModel domain entity <-> LearningModelModel."""

    @staticmethod
    def to_domain(model: LearningModelModel) -> LearningModel:
        """Convert SQLAlchemy model to domain entity."""
        algorithm_version = AlgorithmVersion.parse(model.algorithm_version_str)

        weights_data = json.loads(model.weights_json)
        weights = ScoreWeights(**weights_data)

        active_rules = json.loads(model.active_rules_json)

        return LearningModel(
            id=LearningModelId.from_string(model.id),
            algorithm_version=algorithm_version,
            current_weights=weights,
            minimum_confidence=model.minimum_confidence,
            minimum_sample_size=model.minimum_sample_size,
            active_rules=active_rules,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: LearningModel, version: int = 1) -> LearningModelModel:
        """Convert domain entity to SQLAlchemy model."""
        return LearningModelModel(
            id=str(entity.id),
            algorithm_version_str=str(entity.algorithm_version),
            weights_json=json.dumps(entity.current_weights.as_dict()),
            minimum_confidence=entity.minimum_confidence,
            minimum_sample_size=entity.minimum_sample_size,
            active_rules_json=json.dumps(entity.active_rules),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=version,
        )
