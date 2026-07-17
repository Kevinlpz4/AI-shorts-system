"""Tests for ExplanationService — 6 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.explanation_dto import ExplanationDTO
from learning.application.services.explanation_service import ExplanationService
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.signal_type import SignalType

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestExplanationServiceExplainDecision:
    """Tests for ExplanationService.explain_decision — query (no UoW)."""

    def _make_service_with_model(self, learning_model):
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)

        service = ExplanationService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )
        return service, model_repo, source_quality_repo, signal_repo

    def _make_snapshot(self) -> FeatureSnapshot:
        return FeatureSnapshot(
            base_score=0.75,
            freshness_score=0.80,
            keyword_bonus=0.60,
            source_bonus=0.55,
            topic_penalty=0.10,
            confidence=0.90,
            final_score=0.82,
            timestamp=FIXED_TS,
        )

    def test_explain_decision_with_snapshot(self, learning_model) -> None:
        """Explain with provided FeatureSnapshot → uses snapshot directly."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        snapshot = self._make_snapshot()
        result = service.explain_decision(
            source_name="TechBlog", feature_snapshot=snapshot
        )

        assert result.is_success
        dto = result.value
        assert isinstance(dto, ExplanationDTO)
        assert dto.source_name == "TechBlog"
        assert dto.base_score == 0.75
        assert dto.freshness_score == 0.80
        assert dto.keyword_bonus == 0.60
        assert dto.source_bonus == 0.55
        assert dto.topic_penalty == 0.10
        assert dto.confidence == 0.90
        assert dto.final_score == 0.82
        assert dto.model_version == "1.2.3"

    def test_explain_decision_without_snapshot(self, learning_model) -> None:
        """Explain without snapshot → reconstructs from source quality data."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        mock_profile = MagicMock()
        mock_profile.approval_rate = 0.75
        source_quality_repo.find_by_source_name.return_value = Result.success(
            mock_profile
        )
        signal_repo.find_all_active.return_value = []

        result = service.explain_decision(source_name="TechBlog")

        assert result.is_success
        dto = result.value
        assert isinstance(dto, ExplanationDTO)
        assert dto.source_bonus == 0.75  # from profile approval_rate
        assert dto.source_name == "TechBlog"

    def test_explain_decision_model_not_found(self) -> None:
        """Model not found → failure."""
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )

        service = ExplanationService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )

        result = service.explain_decision(source_name="TechBlog")

        assert result.is_failure

    def test_explain_decision_with_signals(self, learning_model) -> None:
        """Active signals for the source are included in explanation."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        signal1 = MagicMock()
        signal1.signal_type = SignalType.SOURCE
        signal1.dimension = "TechBlog"
        signal2 = MagicMock()
        signal2.signal_type = SignalType.KEYWORD
        signal2.dimension = "TechBlog"
        signal_repo.find_all_active.return_value = [signal1, signal2]

        snapshot = self._make_snapshot()
        result = service.explain_decision(
            source_name="TechBlog", feature_snapshot=snapshot
        )

        assert result.is_success
        assert len(result.value.active_signals) == 2
        assert "SOURCE:TechBlog" in result.value.active_signals
        assert "KEYWORD:TechBlog" in result.value.active_signals

    def test_explain_decision_no_source_profile(self, learning_model) -> None:
        """No source profile → source_bonus defaults to 0.0."""
        service, model_repo, source_quality_repo, signal_repo = (
            self._make_service_with_model(learning_model)
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        result = service.explain_decision(source_name="UnknownSource")

        assert result.is_success
        dto = result.value
        # Without profile, source_bonus should be 0.0
        assert dto.source_bonus == 0.0

    def test_explain_decision_no_uow(self, learning_model) -> None:
        """Queries must NOT call UoW."""
        model_repo = MagicMock()
        source_quality_repo = MagicMock()
        signal_repo = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )
        signal_repo.find_all_active.return_value = []

        service = ExplanationService(
            model_repo=model_repo,
            source_quality_repo=source_quality_repo,
            signal_repo=signal_repo,
        )

        service.explain_decision(source_name="TechBlog")

        # ExplanationService doesn't even have a UoW dependency
        # but verify the repos are called correctly
        model_repo.find_current.assert_called_once()
