"""
FeatureSnapshotMapper — convierte ``FeatureSnapshot`` (domain) → ``ExplanationDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.explanation_dto import ExplanationDTO
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot


class FeatureSnapshotMapper:
    """Mapea FeatureSnapshot a ExplanationDTO."""

    @staticmethod
    def to_dto(
        snapshot: FeatureSnapshot,
        source_name: str,
        model_version: str,
        active_signals: tuple[str, ...],
    ) -> ExplanationDTO:
        """Convierte un FeatureSnapshot a ExplanationDTO.

        Args:
            snapshot: FeatureSnapshot de dominio.
            source_name: Nombre de la fuente.
            model_version: Versión del algoritmo que produjo el score.
            active_signals: Señales activas que influyeron en el score.

        Returns:
            ExplanationDTO con explicación detallada del score.
        """
        return ExplanationDTO(
            source_name=source_name,
            base_score=snapshot.base_score,
            freshness_score=snapshot.freshness_score,
            keyword_bonus=snapshot.keyword_bonus,
            source_bonus=snapshot.source_bonus,
            topic_penalty=snapshot.topic_penalty,
            confidence=snapshot.confidence,
            final_score=snapshot.final_score,
            timestamp=snapshot.timestamp.isoformat(),
            model_version=model_version,
            active_signals=active_signals,
        )
