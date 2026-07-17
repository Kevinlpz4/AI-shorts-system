"""
PredictionService — Casos de uso para predicciones de aprobación.

Servicio puro de consultas. NO modifica datos. Predicción estadística
basada en señales acumuladas, pesos del modelo y umbrales de confianza.

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
from learning.application.dto.prediction_dto import PredictionDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.snapshot_mapper import FeatureSnapshotMapper
from learning.application.queries.prediction_queries import (
    ExplainScoreQuery,
    PredictApprovalQuery,
)
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    LearningModelRepository,
    LearningSignalRepository,
    SourceQualityRepository,
)
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.signal_type import SignalType


class PredictionService:
    """Casos de uso para predicciones de aprobación.

    Solo lectura. NO usa UnitOfWork.
    NO ejecuta IA — usa estadísticas acumuladas, pesos y umbrales.
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

    # ── Queries (solo lectura, sin UoW) ──

    def execute_predict_approval(
        self, query: PredictApprovalQuery
    ) -> Result[PredictionDTO]:
        """Predict approval probability for content from a source.

        NO AI. Uses statistical signals + current weights + confidence +
        thresholds to compute a probability.

        Steps:
            1. Get current LearningModel (weights, thresholds)
            2. Get SourceQualityProfile for the source
            3. Get relevant signals
            4. Calculate probability as weighted sum
            5. Calculate confidence from sample sizes
            6. Build reasoning summary string
            7. Return PredictionDTO
        """
        try:
            # 1. Get current LearningModel
            model_result = self._model_repo.find_current()
            if model_result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(model_result.error)
                )
            model = model_result.value
            weights = model.current_weights

            # 2. Get SourceQualityProfile for the source
            source_result = self._source_quality_repo.find_by_source_name(
                query.source_name
            )

            source_approval_rate = 0.0
            source_sample_size = 0
            if source_result.is_success:
                profile = source_result.value
                source_approval_rate = profile.approval_rate
                source_sample_size = profile.total_decisions

            # 3. Get relevant signals for this source
            all_signals = self._signal_repo.find_all_active()
            source_signals = [
                s for s in all_signals
                if s.signal_type == SignalType.SOURCE
                and s.dimension == query.source_name
            ]
            keyword_signals = [
                s for s in all_signals
                if s.signal_type == SignalType.KEYWORD
            ]

            # 4. Calculate probability as weighted sum
            #    probability = source_rate * source_reliability_weight
            #                + signal_contribution * relevance_weight
            #                + feature_contributions
            probability = source_approval_rate * weights.source_reliability

            # Add signal contribution
            if source_signals:
                avg_signal_strength = sum(
                    s.strength.value for s in source_signals
                ) / len(source_signals)
                probability += avg_signal_strength * weights.relevance

            # Add keyword signal contribution
            if keyword_signals:
                avg_keyword_strength = sum(
                    s.strength.value for s in keyword_signals
                ) / len(keyword_signals)
                probability += avg_keyword_strength * weights.popularity

            # Add feature-based contribution if provided
            if query.features:
                feature_final = query.features.get("final_score", 0.0)
                probability += feature_final * weights.recency

            # Clamp to [0.0, 1.0]
            probability = max(0.0, min(1.0, probability))

            # 5. Calculate confidence from sample sizes
            total_samples = source_sample_size + sum(
                s.sample_size for s in source_signals
            )
            min_sample = model.minimum_sample_size
            confidence = min(1.0, total_samples / max(min_sample, 1))

            # 6. Build reasoning summary
            reasoning_parts: list[str] = []
            reasoning_parts.append(
                f"Source approval rate: {source_approval_rate:.2f} "
                f"(weight: {weights.source_reliability:.2f})"
            )
            if source_signals:
                reasoning_parts.append(
                    f"Source signal strength: "
                    f"{sum(s.strength.value for s in source_signals) / len(source_signals):.2f}"
                )
            if keyword_signals:
                reasoning_parts.append(
                    f"Keyword signals: {len(keyword_signals)} active"
                )
            reasoning_parts.append(
                f"Confidence: {confidence:.2f} "
                f"(samples: {total_samples}, min: {min_sample})"
            )
            reasoning_summary = " | ".join(reasoning_parts)

            # 7. Return PredictionDTO
            return Result.success(
                PredictionDTO(
                    probability=probability,
                    confidence=confidence,
                    reasoning_summary=reasoning_summary,
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

    def execute_explain_score(
        self, query: ExplainScoreQuery
    ) -> Result[ExplanationDTO]:
        """Explain how a score was computed for a source.

        Reconstructs the explanation from existing data.
        NO recalculates rules. Explains what happened.

        Steps:
            1. Get current LearningModel
            2. Get SourceQualityProfile
            3. Get FeatureSnapshot (if available) or reconstruct from signals
            4. Map to ExplanationDTO via FeatureSnapshotMapper
            5. Return ExplanationDTO
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
                query.source_name
            )

            source_bonus = 0.0
            if source_result.is_success:
                source_bonus = source_result.value.approval_rate

            # 3. Build FeatureSnapshot
            if query.features:
                # Use provided features
                now = model.updated_at
                snapshot = FeatureSnapshot(
                    base_score=query.features.get("base_score", 0.0),
                    freshness_score=query.features.get("freshness_score", 0.0),
                    keyword_bonus=query.features.get("keyword_bonus", 0.0),
                    source_bonus=query.features.get("source_bonus", source_bonus),
                    topic_penalty=query.features.get("topic_penalty", 0.0),
                    confidence=query.features.get("confidence", 0.0),
                    final_score=query.features.get("final_score", 0.0),
                    timestamp=now,
                )
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

            # 4. Get active signals for this source
            all_signals = self._signal_repo.find_all_active()
            active_signal_names = tuple(
                f"{s.signal_type.value}:{s.dimension}"
                for s in all_signals
                if s.dimension == query.source_name
            )

            # 5. Map to ExplanationDTO via mapper
            return Result.success(
                FeatureSnapshotMapper.to_dto(
                    snapshot=snapshot,
                    source_name=query.source_name,
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
