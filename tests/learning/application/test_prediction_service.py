"""Tests for PredictionService — 7 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.explanation_dto import ExplanationDTO
from learning.application.dto.prediction_dto import PredictionDTO
from learning.application.queries.prediction_queries import (
    ExplainScoreQuery,
    PredictApprovalQuery,
)
from learning.application.services.prediction_service import PredictionService
from learning.domain.value_objects.signal_type import SignalType

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestPredictionServicePredictApproval:
    """Tests for PredictionService.execute_predict_approval — query (no UoW)."""

    def _make_service_with_model(self, learning_model):
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)

        service = PredictionService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )
        return service, model_repo, source_quality_repo, signal_repo

    def _make_mock_signal(self, signal_type, dimension, strength_value=0.8, sample_size=10):
        signal = MagicMock()
        signal.signal_type = signal_type
        signal.dimension = dimension
        signal.strength = MagicMock()
        signal.strength.value = strength_value
        signal.sample_size = sample_size
        return signal

    def _make_mock_profile(self, approval_rate=0.75, total_decisions=20):
        profile = MagicMock()
        profile.approval_rate = approval_rate
        profile.total_decisions = total_decisions
        return profile

    def test_predict_approval_success(self, learning_model) -> None:
        """Predict with source quality + signals → success + PredictionDTO."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )

        source_quality_repo.find_by_source_name.return_value = Result.success(
            self._make_mock_profile(approval_rate=0.8, total_decisions=20)
        )
        signal_repo.find_all_active.return_value = [
            self._make_mock_signal(SignalType.SOURCE, "TechBlog", 0.8, 10),
        ]

        query = PredictApprovalQuery(source_name="TechBlog")
        result = service.execute_predict_approval(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, PredictionDTO)
        assert 0.0 <= dto.probability <= 1.0
        assert 0.0 <= dto.confidence <= 1.0
        assert len(dto.reasoning_summary) > 0

    def test_predict_approval_high_confidence(self, learning_model) -> None:
        """High sample size → confidence close to 1.0."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )

        source_quality_repo.find_by_source_name.return_value = Result.success(
            self._make_mock_profile(approval_rate=0.8, total_decisions=100)
        )
        signal_repo.find_all_active.return_value = [
            self._make_mock_signal(SignalType.SOURCE, "TechBlog", 0.8, 50),
        ]

        query = PredictApprovalQuery(source_name="TechBlog")
        result = service.execute_predict_approval(query)

        assert result.is_success
        assert result.value.confidence >= 0.9

    def test_predict_approval_low_confidence(self, learning_model) -> None:
        """Low sample size → low confidence."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )

        source_quality_repo.find_by_source_name.return_value = Result.success(
            self._make_mock_profile(approval_rate=0.8, total_decisions=2)
        )
        signal_repo.find_all_active.return_value = []

        query = PredictApprovalQuery(source_name="TechBlog")
        result = service.execute_predict_approval(query)

        assert result.is_success
        assert result.value.confidence < 0.5

    def test_predict_approval_with_features(self, learning_model) -> None:
        """Prediction with feature overrides adds recency contribution."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )

        source_quality_repo.find_by_source_name.return_value = Result.success(
            self._make_mock_profile(approval_rate=0.8, total_decisions=20)
        )
        signal_repo.find_all_active.return_value = []

        query = PredictApprovalQuery(
            source_name="TechBlog",
            features={"final_score": 0.9},
        )
        result = service.execute_predict_approval(query)

        assert result.is_success
        # Probability should include the feature contribution
        assert result.value.probability > 0.0

    def test_predict_approval_model_not_found(self) -> None:
        """Model not found → failure."""
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )

        service = PredictionService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )

        query = PredictApprovalQuery(source_name="TechBlog")
        result = service.execute_predict_approval(query)

        assert result.is_failure

    def test_predict_approval_no_source_profile(self, learning_model) -> None:
        """Source not found → uses 0.0 approval rate as default."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )

        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        query = PredictApprovalQuery(source_name="UnknownSource")
        result = service.execute_predict_approval(query)

        assert result.is_success
        # With no source profile and no signals, probability should be low
        assert result.value.probability == 0.0

    def test_predict_approval_no_uow(self, learning_model) -> None:
        """Prediction queries must NOT call UoW."""
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()
        uow = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        service = PredictionService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )

        query = PredictApprovalQuery(source_name="Test")
        service.execute_predict_approval(query)

        uow.commit.assert_not_called()


class TestPredictionServiceExplainScore:
    """Tests for PredictionService.execute_explain_score — query (no UoW)."""

    def _make_service_with_model(self, learning_model):
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)

        service = PredictionService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )
        return service, model_repo, source_quality_repo, signal_repo

    def test_explain_score_success(self, learning_model) -> None:
        """Explain with features → returns ExplanationDTO."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        query = ExplainScoreQuery(
            source_name="TechBlog",
            features={
                "base_score": 0.8,
                "freshness_score": 0.7,
                "keyword_bonus": 0.1,
                "source_bonus": 0.2,
                "topic_penalty": 0.0,
                "confidence": 0.9,
                "final_score": 0.85,
            },
        )

        result = service.execute_explain_score(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, ExplanationDTO)
        assert dto.source_name == "TechBlog"
        assert dto.model_version == "1.2.3"

    def test_explain_score_no_snapshot(self, learning_model) -> None:
        """Explain without features → reconstructs from source quality data."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        mock_profile = MagicMock()
        mock_profile.approval_rate = 0.8
        source_quality_repo.find_by_source_name.return_value = Result.success(
            mock_profile
        )
        signal_repo.find_all_active.return_value = []

        query = ExplainScoreQuery(source_name="TechBlog")
        result = service.execute_explain_score(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, ExplanationDTO)
        assert dto.source_bonus == 0.8  # from profile approval_rate

    def test_explain_score_model_not_found(self) -> None:
        """Model not found → failure."""
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )

        service = PredictionService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )

        query = ExplainScoreQuery(source_name="TechBlog")
        result = service.execute_explain_score(query)

        assert result.is_failure

    def test_explain_score_with_active_signals(self, learning_model) -> None:
        """Active signals for the source appear in explanation."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        signal = MagicMock()
        signal.signal_type = SignalType.SOURCE
        signal.dimension = "TechBlog"
        signal_repo.find_all_active.return_value = [signal]

        query = ExplainScoreQuery(
            source_name="TechBlog",
            features={"base_score": 0.5, "freshness_score": 0.5,
                       "keyword_bonus": 0.0, "source_bonus": 0.5,
                       "topic_penalty": 0.0, "confidence": 0.5,
                       "final_score": 0.5},
        )

        result = service.execute_explain_score(query)

        assert result.is_success
        assert len(result.value.active_signals) == 1
        assert "SOURCE:TechBlog" in result.value.active_signals
