"""
AnalyticsMapper — convierte datos agregados → ``AnalyticsDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.
"""
from __future__ import annotations

from learning.application.dto.analytics_dto import AnalyticsDTO
from learning.application.dto.source_dto import SourceQualityDTO


class AnalyticsMapper:
    """Mapea datos agregados a AnalyticsDTO."""

    @staticmethod
    def to_dto(
        feedback_count: int,
        signal_count: int,
        avg_rate: float,
        signals_by_dim: dict[str, int],
        top_sources: tuple[SourceQualityDTO, ...],
    ) -> AnalyticsDTO:
        """Convierte datos agregados a AnalyticsDTO.

        Args:
            feedback_count: Número total de feedback records.
            signal_count: Número total de señales de aprendizaje.
            avg_rate: Tasa de aprobación promedio (0.0-1.0).
            signals_by_dim: Conteo de señales por dimensión.
            top_sources: Fuentes con mejor rendimiento.

        Returns:
            AnalyticsDTO con analíticas generales.
        """
        return AnalyticsDTO(
            total_feedback=feedback_count,
            total_signals=signal_count,
            average_approval_rate=avg_rate,
            signals_by_dimension=signals_by_dim,
            top_sources=top_sources,
        )
