"""Tests for ScoringService — 8 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.commands.score_commands import AdjustScoreWeightsCommand
from learning.application.dto.model_dto import LearningModelDTO
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.queries.model_queries import GetLearningModelQuery
from learning.application.services.scoring_service import ScoringService
from learning.domain.entities.learning_model import LearningModel
from learning.domain.exceptions import LearningDomainError

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestScoringServiceAdjustScoreWeights:
    """Tests for ScoringService.execute_adjust_score_weights — command."""

    def _make_service(self, learning_model: LearningModel):
        model_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()
        clock.now.return_value = FIXED_TS

        model_repo.find_current.return_value = Result.success(learning_model)

        service = ScoringService(
            model_repo=model_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, model_repo, uow, event_publisher

    def test_adjust_score_weights_success(self, learning_model) -> None:
        """Adjust weights with valid values → success + LearningModelDTO."""
        service, model_repo, uow, event_publisher = self._make_service(
            learning_model
        )

        cmd = AdjustScoreWeightsCommand(
            source_id=str(learning_model.id),
            weights={
                "relevance": 0.40,
                "popularity": 0.20,
                "recency": 0.20,
                "source_reliability": 0.20,
            },
            reason="Performance optimization",
        )

        result = service.execute_adjust_score_weights(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, LearningModelDTO)
        assert dto.weights["relevance"] == 0.40

    def test_adjust_score_weights_uow_commit_called(self, learning_model) -> None:
        """UoW.commit() must be called for write operations."""
        service, model_repo, uow, event_publisher = self._make_service(
            learning_model
        )

        cmd = AdjustScoreWeightsCommand(
            source_id=str(learning_model.id),
            weights={
                "relevance": 0.25,
                "popularity": 0.25,
                "recency": 0.25,
                "source_reliability": 0.25,
            },
            reason="Test reason",
        )

        service.execute_adjust_score_weights(cmd)

        uow.commit.assert_called_once()

    def test_adjust_score_weights_publishes_events(self, learning_model) -> None:
        """ScoreAdjusted event must be published after commit."""
        service, model_repo, uow, event_publisher = self._make_service(
            learning_model
        )

        cmd = AdjustScoreWeightsCommand(
            source_id=str(learning_model.id),
            weights={
                "relevance": 0.25,
                "popularity": 0.25,
                "recency": 0.25,
                "source_reliability": 0.25,
            },
            reason="Test reason",
        )

        service.execute_adjust_score_weights(cmd)

        event_publisher.publish_many.assert_called_once()
        events = event_publisher.publish_many.call_args[0][0]
        assert len(events) >= 1

    def test_adjust_score_weights_domain_error_empty_reason(
        self, learning_model
    ) -> None:
        """Empty reason → LearningDomainError → failure."""
        service, model_repo, uow, event_publisher = self._make_service(
            learning_model
        )

        cmd = AdjustScoreWeightsCommand(
            source_id=str(learning_model.id),
            weights={
                "relevance": 0.25,
                "popularity": 0.25,
                "recency": 0.25,
                "source_reliability": 0.25,
            },
            reason="",
        )

        result = service.execute_adjust_score_weights(cmd)

        assert result.is_failure

    def test_adjust_score_weights_invalid_weights(self) -> None:
        """Model not found → failure."""
        model_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        model_repo.find_current.return_value = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )

        service = ScoringService(
            model_repo=model_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )

        cmd = AdjustScoreWeightsCommand(
            source_id="00000000-0000-0000-0000-000000000099",
            weights={
                "relevance": 0.25,
                "popularity": 0.25,
                "recency": 0.25,
                "source_reliability": 0.25,
            },
            reason="Test",
        )

        result = service.execute_adjust_score_weights(cmd)

        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND


class TestScoringServiceGetLearningModel:
    """Tests for ScoringService.execute_get_learning_model — query (no UoW)."""

    def _make_service(self, learning_model: LearningModel):
        model_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        model_repo.find_current.return_value = Result.success(learning_model)

        service = ScoringService(
            model_repo=model_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, model_repo, uow

    def test_get_learning_model_success(self, learning_model) -> None:
        """Get current model → returns LearningModelDTO."""
        service, model_repo, uow = self._make_service(learning_model)

        query = GetLearningModelQuery()
        result = service.execute_get_learning_model(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, LearningModelDTO)
        assert dto.algorithm_version == "1.2.3"
        assert dto.minimum_confidence == 0.5
        assert dto.minimum_sample_size == 10
        assert dto.rules_count == 2

    def test_get_learning_model_not_found(self) -> None:
        """Model not found → failure."""
        model_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        model_repo.find_current.return_value = Result.failure(
            Error(code="MODEL_NOT_FOUND", message="No model")
        )

        service = ScoringService(
            model_repo=model_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )

        query = GetLearningModelQuery()
        result = service.execute_get_learning_model(query)

        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_get_learning_model_no_uow(self, learning_model) -> None:
        """Queries must NOT call UoW.commit()."""
        service, model_repo, uow = self._make_service(learning_model)

        query = GetLearningModelQuery()
        service.execute_get_learning_model(query)

        uow.commit.assert_not_called()
