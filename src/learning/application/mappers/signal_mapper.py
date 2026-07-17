"""
LearningSignalMapper — convierte ``LearningSignal`` (domain) → ``LearningSignalDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.signal_dto import LearningSignalDTO
from learning.domain.entities.learning_signal import LearningSignal


class LearningSignalMapper:
    """Mapea entidades LearningSignal a DTOs de aplicación."""

    @staticmethod
    def to_dto(entity: LearningSignal) -> LearningSignalDTO:
        """Convierte una entidad LearningSignal a LearningSignalDTO.

        Args:
            entity: Entidad de dominio LearningSignal.

        Returns:
            LearningSignalDTO con datos de la señal.
        """
        return LearningSignalDTO(
            id=str(entity.id),
            dimension=entity.signal_type.value,
            source=entity.dimension,
            sample_size=entity.sample_size,
            approval_rate=entity.approval_rate,
            strength=entity.strength.value,
            decay_factor=entity.strength.decay_factor,
            updated_at=entity.last_updated.isoformat(),
        )
