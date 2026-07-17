"""Tests for RecommendationService — 7 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.explanation_dto import ExplanationDTO
from learning.application.dto.prediction_dto import PredictionDTO
from learning.application.dto.recommendation_dto import RecommendationDTO
from learning.application.services.recommendation_service import RecommendationService

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestRecommendationServiceRecommend:
    """Tests for RecommendationService.recommend — query (no UoW)."""

    def _make_service(self, prediction_result, explanation_result):
        prediction_service = MagicMock()
        explanation_service = MagicMock()
        source_quality_repo = MagicMock()
        model_repo = MagicMock()

        prediction_service.execute_predict_approval.return_value = prediction_result
        explanation_service.execute_explain_score.return_value = explanation_result

        service = RecommendationService(
            prediction_service=prediction_service,
            explanation_service=explanation_service,
            source_quality_repo=source_quality_repo,
            model_repo=model_repo,
        )
        return service, prediction_service, explanation_service, source_quality_repo, model_repo

    def test_recommend_approve(self) -> None:
        """High probability (>= 0.7) → APPROVE recommendation."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.85,
                confidence=0.9,
                reasoning_summary="High approval rate",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="TechBlog",
                base_score=0.8,
                freshness_score=0.7,
                keyword_bonus=0.1,
                source_bonus=0.8,
                topic_penalty=0.0,
                confidence=0.9,
                final_score=0.85,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=("SOURCE:TechBlog",),
            )
        )

        service, _, _, _, _ = self._make_service(
            prediction_result, explanation_result
        )

        result = service.recommend(source_name="TechBlog")

        assert result.is_success
        dto = result.value
        assert isinstance(dto, RecommendationDTO)
        assert dto.recommendation == "APPROVE"
        assert dto.probability == 0.85
        assert dto.confidence == 0.9

    def test_recommend_reject(self) -> None:
        """Low probability (< 0.3) → REJECT recommendation."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.15,
                confidence=0.8,
                reasoning_summary="Low approval rate",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="SpamSource",
                base_score=0.1,
                freshness_score=0.2,
                keyword_bonus=0.0,
                source_bonus=0.15,
                topic_penalty=0.3,
                confidence=0.8,
                final_score=0.15,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=(),
            )
        )

        service, _, _, _, _ = self._make_service(
            prediction_result, explanation_result
        )

        result = service.recommend(source_name="SpamSource")

        assert result.is_success
        assert result.value.recommendation == "REJECT"
        assert result.value.probability == 0.15

    def test_recommend_manual_review(self) -> None:
        """Probability between 0.3 and 0.7 → MANUAL_REVIEW recommendation."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.50,
                confidence=0.6,
                reasoning_summary="Moderate approval rate",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="MediumSource",
                base_score=0.5,
                freshness_score=0.5,
                keyword_bonus=0.0,
                source_bonus=0.5,
                topic_penalty=0.0,
                confidence=0.6,
                final_score=0.5,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=(),
            )
        )

        service, _, _, _, _ = self._make_service(
            prediction_result, explanation_result
        )

        result = service.recommend(source_name="MediumSource")

        assert result.is_success
        assert result.value.recommendation == "MANUAL_REVIEW"
        assert result.value.probability == 0.50

    def test_recommend_includes_reasoning(self) -> None:
        """Reasoning tuple is not empty and includes prediction summary."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.8,
                confidence=0.9,
                reasoning_summary="Source approval rate: 0.80",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="TechBlog",
                base_score=0.8,
                freshness_score=0.7,
                keyword_bonus=0.1,
                source_bonus=0.8,
                topic_penalty=0.0,
                confidence=0.9,
                final_score=0.85,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=("SOURCE:TechBlog",),
            )
        )

        service, _, _, _, _ = self._make_service(
            prediction_result, explanation_result
        )

        result = service.recommend(source_name="TechBlog")

        assert result.is_success
        assert len(result.value.reasoning) > 0
        assert "Source approval rate: 0.80" in result.value.reasoning[0]

    def test_recommend_source_quality_rate(self) -> None:
        """Source quality rate from repo is included in DTO."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.8,
                confidence=0.9,
                reasoning_summary="Good",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="TechBlog",
                base_score=0.8,
                freshness_score=0.7,
                keyword_bonus=0.1,
                source_bonus=0.8,
                topic_penalty=0.0,
                confidence=0.9,
                final_score=0.85,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=(),
            )
        )

        service, _, _, source_quality_repo, _ = self._make_service(
            prediction_result, explanation_result
        )

        mock_profile = MagicMock()
        mock_profile.approval_rate = 0.75
        source_quality_repo.find_by_source_name.return_value = Result.success(
            mock_profile
        )

        result = service.recommend(source_name="TechBlog")

        assert result.is_success
        assert result.value.source_quality == 0.75

    def test_recommend_model_version(self) -> None:
        """Model version from repo is included in DTO."""
        prediction_result = Result.success(
            PredictionDTO(
                probability=0.8,
                confidence=0.9,
                reasoning_summary="Good",
            )
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="TechBlog",
                base_score=0.8,
                freshness_score=0.7,
                keyword_bonus=0.1,
                source_bonus=0.8,
                topic_penalty=0.0,
                confidence=0.9,
                final_score=0.85,
                timestamp=FIXED_TS.isoformat(),
                model_version="1.2.3",
                active_signals=(),
            )
        )

        service, _, _, _, model_repo = self._make_service(
            prediction_result, explanation_result
        )

        mock_model = MagicMock()
        mock_model.algorithm_version = "2.0.1"
        model_repo.find_current.return_value = Result.success(mock_model)

        result = service.recommend(source_name="TechBlog")

        assert result.is_success
        assert result.value.model_version == "2.0.1"

    def test_recommend_prediction_failure(self) -> None:
        """If prediction fails, recommendation fails."""
        prediction_result = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )
        explanation_result = Result.success(
            ExplanationDTO(
                source_name="TechBlog",
                base_score=0.0,
                freshness_score=0.0,
                keyword_bonus=0.0,
                source_bonus=0.0,
                topic_penalty=0.0,
                confidence=0.0,
                final_score=0.0,
                timestamp=FIXED_TS.isoformat(),
                model_version="unknown",
                active_signals=(),
            )
        )

        service, _, _, _, _ = self._make_service(
            prediction_result, explanation_result
        )

        result = service.recommend(source_name="TechBlog")

        assert result.is_failure
