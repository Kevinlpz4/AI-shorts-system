"""
AnalyticsService — Casos de uso para analytics del sistema de aprendizaje.

Orquesta consultas de analíticas que agregan datos de múltiples repositorios.
Solo lectura — NO modifica datos.

Dependencias inyectadas (DIP):
    - feedback_repo: FeedbackRepository
    - signal_repo: LearningSignalRepository
    - source_quality_repo: SourceQualityRepository

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from foundation.errors import DomainError
from foundation.result.result import Error, Result

from learning.application.dto.analytics_dto import AnalyticsDTO
from learning.application.dto.source_dto import SourceQualityDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.analytics_mapper import AnalyticsMapper
from learning.application.mappers.source_mapper import SourceQualityMapper
from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    FeedbackRepository,
    LearningSignalRepository,
    SourceQualityRepository,
)


class AnalyticsService:
    """Casos de uso para analytics del sistema de aprendizaje.

    Solo lectura. NO usa UnitOfWork.
    Agrega datos de múltiples repositorios para producir analíticas.
    """

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        signal_repo: LearningSignalRepository,
        source_quality_repo: SourceQualityRepository,
    ) -> None:
        self._feedback_repo = feedback_repo
        self._signal_repo = signal_repo
        self._source_quality_repo = source_quality_repo

    # ── Queries (solo lectura, sin UoW) ──

    def execute_get_analytics(
        self, query: GetAnalyticsQuery
    ) -> Result[AnalyticsDTO]:
        """Aggregate analytics across the system.

        Solo lectura. Sin UnitOfWork.

        Steps:
            1. Count total feedback (from each decision type)
            2. Count total signals
            3. Calculate average approval rate from SourceQualityProfiles
            4. Group signals by dimension
            5. Get top sources by approval rate
            6. Return AnalyticsDTO
        """
        try:
            from learning.domain.value_objects.decision_type import DecisionType

            # 1. Count total feedback across all decision types
            total_feedback = 0
            for dt in DecisionType:
                total_feedback += self._feedback_repo.count_by_decision(dt)

            # 2. Count total active signals
            active_signals = self._signal_repo.find_all_active()
            total_signals = len(active_signals)

            # 3. Calculate average approval rate from SourceQualityProfiles
            active_profiles = self._source_quality_repo.find_all_active()
            if active_profiles:
                avg_approval_rate = sum(
                    p.approval_rate for p in active_profiles
                ) / len(active_profiles)
            else:
                avg_approval_rate = 0.0

            # 4. Group signals by dimension
            signals_by_dimension: dict[str, int] = {}
            for signal in active_signals:
                dim = signal.signal_type.value
                signals_by_dimension[dim] = signals_by_dimension.get(dim, 0) + 1

            # 5. Get top sources by approval rate (sorted descending)
            top_profiles = sorted(
                active_profiles,
                key=lambda p: p.approval_rate,
                reverse=True,
            )
            top_sources: tuple[SourceQualityDTO, ...] = tuple(
                SourceQualityMapper.to_dto(p) for p in top_profiles[:10]
            )

            # 6. Build and return DTO via mapper
            return Result.success(
                AnalyticsMapper.to_dto(
                    feedback_count=total_feedback,
                    signal_count=total_signals,
                    avg_rate=avg_approval_rate,
                    signals_by_dim=signals_by_dimension,
                    top_sources=top_sources,
                )
            )

        except LearningDomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )
