"""
FeedbackMapper — convierte ``FeedbackRecord`` (domain) → ``FeedbackSummaryDTO`` / ``FeedbackDetailDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.feedback_dto import FeedbackDetailDTO, FeedbackSummaryDTO
from learning.domain.entities.feedback_record import FeedbackRecord


class FeedbackMapper:
    """Mapea entidades FeedbackRecord a DTOs de aplicación."""

    @staticmethod
    def to_summary(entity: FeedbackRecord) -> FeedbackSummaryDTO:
        """Convierte una entidad FeedbackRecord a FeedbackSummaryDTO.

        Args:
            entity: Entidad de dominio FeedbackRecord.

        Returns:
            FeedbackSummaryDTO con datos básicos.
        """
        return FeedbackSummaryDTO(
            id=str(entity.id),
            topic_id=entity.topic_id,
            decision=entity.decision.value,
            source_name=entity.source_name,
            created_at=entity.captured_at.isoformat(),
        )

    @staticmethod
    def to_detail(entity: FeedbackRecord) -> FeedbackDetailDTO:
        """Convierte una entidad FeedbackRecord a FeedbackDetailDTO.

        Incluye razón y features de scoring.

        Args:
            entity: Entidad de dominio FeedbackRecord.

        Returns:
            FeedbackDetailDTO con datos completos.
        """
        # Map FeatureSnapshot to dict[str, float] (excluding timestamp)
        features: dict[str, float] | None = None
        if entity.feature_snapshot is not None:
            features = {
                "base_score": entity.feature_snapshot.base_score,
                "freshness_score": entity.feature_snapshot.freshness_score,
                "keyword_bonus": entity.feature_snapshot.keyword_bonus,
                "source_bonus": entity.feature_snapshot.source_bonus,
                "topic_penalty": entity.feature_snapshot.topic_penalty,
                "confidence": entity.feature_snapshot.confidence,
                "final_score": entity.feature_snapshot.final_score,
            }

        return FeedbackDetailDTO(
            id=str(entity.id),
            topic_id=entity.topic_id,
            decision=entity.decision.value,
            reason=entity.reason,
            source_name=entity.source_name,
            title=entity.title,
            features=features,
            created_at=entity.captured_at.isoformat(),
        )
