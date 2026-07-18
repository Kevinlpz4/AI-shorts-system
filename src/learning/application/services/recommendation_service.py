"""
RecommendationService — Casos de uso para recomendaciones de contenido.

El diferenciador. Usa PredictionService + ExplanationService para generar
recomendaciones accionables para el usuario. NO ejecuta IA — usa información
acumulada para ayudar al usuario a decidir.

Dependencias inyectadas (DIP):
    - prediction_service: PredictionService
    - explanation_service: ExplanationService
    - source_quality_repo: SourceQualityRepository
    - model_repo: LearningModelRepository

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from foundation.errors import DomainError
from foundation.result.result import Error, Result

from learning.application.dto.recommendation_dto import RecommendationDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.queries.prediction_queries import (
    PredictApprovalQuery,
)
from learning.application.services.explanation_service import ExplanationService
from learning.application.services.prediction_service import PredictionService
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import (
    LearningModelRepository,
    SourceQualityRepository,
)
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot

# Recommendation thresholds
_APPROVAL_THRESHOLD = 0.7
_REJECTION_THRESHOLD = 0.3


class RecommendationService:
    """Casos de uso para recomendaciones de contenido.

    Solo lectura. NO usa UnitOfWork.
    NO ejecuta IA — usa información acumulada.
    """

    def __init__(
        self,
        prediction_service: PredictionService,
        explanation_service: ExplanationService,
        source_quality_repo: SourceQualityRepository,
        model_repo: LearningModelRepository,
    ) -> None:
        self._prediction_service = prediction_service
        self._explanation_service = explanation_service
        self._source_quality_repo = source_quality_repo
        self._model_repo = model_repo

    def recommend(
        self,
        source_name: str,
        features: dict[str, float] | None = None,
    ) -> Result[RecommendationDTO]:
        """Generate a recommendation for new content.

        NO AI. Uses accumulated information to help the user decide.

        Steps:
            1. Get prediction from PredictionService
            2. Get explanation from ExplanationService
            3. Build recommendation based on thresholds
            4. Include reasoning from explanation
            5. Return RecommendationDTO
        """
        try:
            # 1. Get prediction
            prediction_query = PredictApprovalQuery(
                source_name=source_name,
                features=features,
            )
            prediction_result = self._prediction_service.execute_predict_approval(
                prediction_query
            )
            if prediction_result.is_failure:
                return Result.failure(
                    ErrorMapper.map_result_error(prediction_result.error)
                )
            prediction = prediction_result.value

            # 2. Get explanation
            #    Build FeatureSnapshot from features dict if provided
            feature_snapshot = None
            if features:
                from datetime import datetime, timezone

                feature_snapshot = FeatureSnapshot(
                    base_score=features.get("base_score", 0.0),
                    freshness_score=features.get("freshness_score", 0.0),
                    keyword_bonus=features.get("keyword_bonus", 0.0),
                    source_bonus=features.get("source_bonus", 0.0),
                    topic_penalty=features.get("topic_penalty", 0.0),
                    confidence=features.get("confidence", 0.0),
                    final_score=features.get("final_score", 0.0),
                    timestamp=datetime.now(timezone.utc),
                )
            explanation_result = self._explanation_service.explain_decision(
                source_name=source_name,
                feature_snapshot=feature_snapshot,
            )

            # 3. Build recommendation based on thresholds
            probability = prediction.probability
            if probability >= _APPROVAL_THRESHOLD:
                recommendation = "APPROVE"
            elif probability < _REJECTION_THRESHOLD:
                recommendation = "REJECT"
            else:
                recommendation = "MANUAL_REVIEW"

            # 4. Build reasoning
            reasoning: list[str] = []
            reasoning.append(prediction.reasoning_summary)

            if explanation_result.is_success:
                explanation = explanation_result.value
                reasoning.append(
                    f"Source quality: {explanation.source_bonus:.2f}"
                )
                reasoning.append(
                    f"Model version: {explanation.model_version}"
                )
                if explanation.active_signals:
                    reasoning.append(
                        f"Active signals: {len(explanation.active_signals)}"
                    )

            # 5. Get source quality rate
            source_quality_rate = 0.0
            source_result = self._source_quality_repo.find_by_source_name(
                source_name
            )
            if source_result.is_success:
                source_quality_rate = source_result.value.approval_rate

            # 6. Get model version
            model_version = "unknown"
            model_result = self._model_repo.find_current()
            if model_result.is_success:
                model_version = str(model_result.value.algorithm_version)

            # 7. Return RecommendationDTO
            return Result.success(
                RecommendationDTO(
                    recommendation=recommendation,
                    probability=probability,
                    confidence=prediction.confidence,
                    reasoning=tuple(reasoning),
                    source_quality=source_quality_rate,
                    model_version=model_version,
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
