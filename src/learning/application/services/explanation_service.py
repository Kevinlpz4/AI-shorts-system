"""
ExplanationService — Servicio dedicado de explicabilidad.

Base para Explainable AI (XAI). Explica decisiones de scoring usando
FeatureSnapshot, LearningModel y señales acumuladas.
Solo lectura — NO modifica datos y NO recalcula reglas.

Dependencias inyectadas (DIP):
    - model_repo: LearningModelRepository
    - source_quality_repo: SourceQualityRepository
    - signal_repo: LearningSignalRepository

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from foundation.errors import DomainError
from foundation.result.result import Error, Result

from learning.application.dto.explanation_dto import ExplanationDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.snapshot_mapper import FeatureSnapshotMapper
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    LearningModelRepository,
    LearningSignalRepository,
    SourceQualityRepository,
)
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.signal_type import SignalType


class ExplanationService:
    """Servicio dedicado de explicabilidad.

    Solo lectura. NO usa UnitOfWork.
    NO recalcula reglas — explica exactamente qué ocurrió.
    """

    def __init__(
        self,
        model_repo: LearningModelRepository,
        source_quality_repo: SourceQualityRepository,
        signal_repo: LearningSignalRepository,
    ) -> None:
        self._model_repo = model_repo
        self._source_quality_repo = source_quality_repo
        self._signal_repo = signal_repo

    def explain_decision(
        self,
        source_name: str,
        feature_snapshot: FeatureSnapshot | None = None,
    ) -> Result[ExplanationDTO]:
        """Explain a decision using FeatureSnapshot + LearningModel + Signals.

        Steps:
            1. Get current LearningModel (version, weights)
            2. Get SourceQualityProfile
            3. Get active signals for this source
            4. If feature_snapshot provided: use it directly
            5. If not: reconstruct from current data (best effort)
            6. Map to ExplanationDTO
            7. Return ExplanationDTO
        """
        try:
            # 1. Get current LearningModel
            model_result = self._model_repo.find_current()
            if model_result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(model_result.error)
                )
            model = model_result.value

            # 2. Get SourceQualityProfile
            source_result = self._source_quality_repo.find_by_source_name(
                source_name
            )

            source_bonus = 0.0
            if source_result.is_success:
                source_bonus = source_result.value.approval_rate

            # 3. Get active signals for this source
            all_signals = self._signal_repo.find_all_active()
            active_signal_names = tuple(
                f"{s.signal_type.value}:{s.dimension}"
                for s in all_signals
                if s.dimension == source_name
            )

            # 4-5. Build or use provided FeatureSnapshot
            if feature_snapshot is not None:
                snapshot = feature_snapshot
            else:
                # Reconstruct from current data (best effort)
                from datetime import datetime, timezone

                now = datetime.now(timezone.utc)
                snapshot = FeatureSnapshot(
                    base_score=0.0,
                    freshness_score=0.0,
                    keyword_bonus=0.0,
                    source_bonus=source_bonus,
                    topic_penalty=0.0,
                    confidence=0.0,
                    final_score=source_bonus,
                    timestamp=now,
                )

            # 6. Map to ExplanationDTO via mapper
            return Result.success(
                FeatureSnapshotMapper.to_dto(
                    snapshot=snapshot,
                    source_name=source_name,
                    model_version=str(model.algorithm_version),
                    active_signals=active_signal_names,
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
