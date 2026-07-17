"""Tests for AnalyticsService — 6 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.dto.analytics_dto import AnalyticsDTO
from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.application.services.analytics_service import AnalyticsService
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestAnalyticsServiceGetAnalytics:
    """Tests for AnalyticsService.execute_get_analytics — query (no UoW)."""

    def _make_service(self):
        feedback_repo = MagicMock()
        signal_repo = MagicMock()
        source_quality_repo = MagicMock()

        service = AnalyticsService(
            feedback_repo=feedback_repo,
            signal_repo=signal_repo,
            source_quality_repo=source_quality_repo,
        )
        return service, feedback_repo, signal_repo, source_quality_repo

    def _make_mock_signal(self, signal_type: SignalType, dimension: str):
        """Create a mock signal with necessary attributes."""
        signal = MagicMock()
        signal.signal_type = signal_type
        signal.dimension = dimension
        signal.strength = MagicMock()
        signal.strength.value = 0.8
        signal.sample_size = 10
        return signal

    def _make_mock_profile(
        self, source_name: str, approval_rate: float, total_decisions: int
    ):
        """Create a mock SourceQualityProfile with necessary attributes."""
        profile = MagicMock()
        profile.source_name = source_name
        profile.approval_rate = approval_rate
        profile.total_decisions = total_decisions
        profile.approved_count = int(total_decisions * approval_rate)
        profile.rejected_count = total_decisions - profile.approved_count
        profile.overridden_count = 0
        profile.keywords = {}
        return profile

    def test_get_analytics_success(self) -> None:
        """Aggregate from 3 repos → success + AnalyticsDTO."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        # Feedback counts
        feedback_repo.count_by_decision.side_effect = lambda dt: {
            DecisionType.APPROVED: 15,
            DecisionType.REJECTED: 5,
            DecisionType.AUTO_APPROVED: 3,
            DecisionType.AUTO_REJECTED: 1,
            DecisionType.OVERRIDDEN: 1,
        }.get(dt, 0)

        # Active signals
        signal1 = self._make_mock_signal(SignalType.KEYWORD, "python")
        signal2 = self._make_mock_signal(SignalType.SOURCE, "TechBlog")
        signal_repo.find_all_active.return_value = [signal1, signal2]

        # Source quality profiles
        profile = self._make_mock_profile("TechBlog", 0.75, 20)
        source_quality_repo.find_all_active.return_value = [profile]

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, AnalyticsDTO)
        assert dto.total_feedback == 25
        assert dto.total_signals == 2
        assert dto.average_approval_rate == 0.75
        assert "KEYWORD" in dto.signals_by_dimension
        assert dto.signals_by_dimension["KEYWORD"] == 1
        assert dto.signals_by_dimension["SOURCE"] == 1

    def test_get_analytics_empty(self) -> None:
        """All repos empty → AnalyticsDTO with zeros."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        feedback_repo.count_by_decision.return_value = 0
        signal_repo.find_all_active.return_value = []
        source_quality_repo.find_all_active.return_value = []

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, AnalyticsDTO)
        assert dto.total_feedback == 0
        assert dto.total_signals == 0
        assert dto.average_approval_rate == 0.0
        assert dto.signals_by_dimension == {}
        assert len(dto.top_sources) == 0

    def test_get_analytics_partial(self) -> None:
        """Some repos have data → aggregates correctly."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        # Only approved feedback exists
        def count_by_decision(dt):
            if dt == DecisionType.APPROVED:
                return 10
            return 0

        feedback_repo.count_by_decision.side_effect = count_by_decision

        # No signals
        signal_repo.find_all_active.return_value = []

        # One profile
        profile = self._make_mock_profile("SourceA", 0.8, 10)
        source_quality_repo.find_all_active.return_value = [profile]

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        dto = result.value
        assert dto.total_feedback == 10
        assert dto.total_signals == 0
        assert dto.average_approval_rate == 0.8

    def test_get_analytics_top_sources_sorted(self) -> None:
        """Top sources must be sorted by approval_rate descending."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        feedback_repo.count_by_decision.return_value = 0
        signal_repo.find_all_active.return_value = []

        # Multiple profiles with different approval rates
        profile_a = self._make_mock_profile("SourceA", 0.6, 10)
        profile_b = self._make_mock_profile("SourceB", 0.9, 10)
        profile_c = self._make_mock_profile("SourceC", 0.3, 10)
        source_quality_repo.find_all_active.return_value = [
            profile_a,
            profile_b,
            profile_c,
        ]

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        top_sources = result.value.top_sources
        assert len(top_sources) == 3
        # First should be highest approval rate
        assert top_sources[0].approval_rate >= top_sources[1].approval_rate
        assert top_sources[1].approval_rate >= top_sources[2].approval_rate

    def test_get_analytics_multiple_signals_same_dimension(self) -> None:
        """Signals of same dimension are grouped correctly."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        feedback_repo.count_by_decision.return_value = 0

        # 3 KEYWORD signals, 1 SOURCE signal
        signals = [
            self._make_mock_signal(SignalType.KEYWORD, "python"),
            self._make_mock_signal(SignalType.KEYWORD, "rust"),
            self._make_mock_signal(SignalType.KEYWORD, "go"),
            self._make_mock_signal(SignalType.SOURCE, "TechBlog"),
        ]
        signal_repo.find_all_active.return_value = signals
        source_quality_repo.find_all_active.return_value = []

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        dto = result.value
        assert dto.signals_by_dimension["KEYWORD"] == 3
        assert dto.signals_by_dimension["SOURCE"] == 1
        assert dto.total_signals == 4

    def test_get_analytics_top_sources_max_10(self) -> None:
        """Top sources capped at 10."""
        service, feedback_repo, signal_repo, source_quality_repo = (
            self._make_service()
        )

        feedback_repo.count_by_decision.return_value = 0
        signal_repo.find_all_active.return_value = []

        # 15 profiles
        profiles = [
            self._make_mock_profile(f"Source{i}", 0.5 + i * 0.03, 10)
            for i in range(15)
        ]
        source_quality_repo.find_all_active.return_value = profiles

        query = GetAnalyticsQuery()
        result = service.execute_get_analytics(query)

        assert result.is_success
        assert len(result.value.top_sources) == 10
