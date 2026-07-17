"""
LearningModelMapper — convierte ``LearningModel`` (domain) → ``LearningModelDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.model_dto import LearningModelDTO
from learning.domain.entities.learning_model import LearningModel


class LearningModelMapper:
    """Mapea entidades LearningModel a DTOs de aplicación."""

    @staticmethod
    def to_dto(entity: LearningModel) -> LearningModelDTO:
        """Convierte una entidad LearningModel a LearningModelDTO.

        Args:
            entity: Entidad de dominio LearningModel.

        Returns:
            LearningModelDTO con datos del modelo de aprendizaje.
        """
        return LearningModelDTO(
            id=str(entity.id),
            algorithm_version=str(entity.algorithm_version),
            weights=entity.current_weights.as_dict(),
            minimum_confidence=entity.minimum_confidence,
            minimum_sample_size=entity.minimum_sample_size,
            rules_count=len(entity.active_rules),
        )
