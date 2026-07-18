"""
Tests for Composition Root — LearningServiceFactory wiring.

Covers:
- build_all returns all 8 services
- build_all with custom clock
- All services are correct types
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.application.services.analytics_service import AnalyticsService
from learning.application.services.dataset_service import DatasetService
from learning.application.services.decision_service import DecisionService
from learning.application.services.explanation_service import ExplanationService
from learning.application.services.prediction_service import PredictionService
from learning.application.services.recommendation_service import RecommendationService
from learning.application.services.scoring_service import ScoringService
from learning.application.services.signal_service import SignalService
from learning.infrastructure.composition import LearningServiceFactory
from learning.infrastructure.inmemory.clock import LearningFrozenClock, LearningSystemClock


# ===========================================================================
# LearningServiceFactory
# ===========================================================================


class TestLearningServiceFactory:
    """Tests for the Learning Composition Root."""

    def test_build_all_returns_all_services(self) -> None:
        """build_all returns a dict with all 8 service keys."""
        factory = LearningServiceFactory()
        services = factory.build_all()

        expected_keys = {
            "decision_service",
            "signal_service",
            "scoring_service",
            "dataset_service",
            "analytics_service",
            "prediction_service",
            "explanation_service",
            "recommendation_service",
        }
        assert set(services.keys()) == expected_keys
        assert len(services) == 8

    def test_build_all_with_custom_clock(self) -> None:
        """Factory accepts a custom clock and wires it to all services."""
        frozen = LearningFrozenClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
        factory = LearningServiceFactory(clock=frozen)

        assert factory.clock is frozen
        services = factory.build_all()
        assert len(services) == 8

    def test_all_services_are_correct_type(self) -> None:
        """Each service in build_all is the expected class."""
        factory = LearningServiceFactory()
        services = factory.build_all()

        assert isinstance(services["decision_service"], DecisionService)
        assert isinstance(services["signal_service"], SignalService)
        assert isinstance(services["scoring_service"], ScoringService)
        assert isinstance(services["dataset_service"], DatasetService)
        assert isinstance(services["analytics_service"], AnalyticsService)
        assert isinstance(services["prediction_service"], PredictionService)
        assert isinstance(services["explanation_service"], ExplanationService)
        assert isinstance(services["recommendation_service"], RecommendationService)

    def test_default_clock_is_system_clock(self) -> None:
        """Without a clock argument, LearningSystemClock is used."""
        factory = LearningServiceFactory()
        assert isinstance(factory.clock, LearningSystemClock)

    def test_infrastructure_accessors(self) -> None:
        """Infrastructure accessors return InMemory implementations."""
        factory = LearningServiceFactory()

        from learning.infrastructure.inmemory.repositories import (
            InMemoryFeedbackRepository,
            InMemoryLearningModelRepository,
            InMemoryLearningSignalRepository,
            InMemorySourceQualityRepository,
        )
        from learning.infrastructure.inmemory.unit_of_work import InMemoryLearningUnitOfWork
        from learning.infrastructure.inmemory.event_publisher import InMemoryLearningEventPublisher
        from learning.infrastructure.inmemory.dataset_exporter import InMemoryDatasetExporter

        assert isinstance(factory.feedback_repo, InMemoryFeedbackRepository)
        assert isinstance(factory.signal_repo, InMemoryLearningSignalRepository)
        assert isinstance(factory.source_quality_repo, InMemorySourceQualityRepository)
        assert isinstance(factory.model_repo, InMemoryLearningModelRepository)
        assert isinstance(factory.uow, InMemoryLearningUnitOfWork)
        assert isinstance(factory.event_publisher, InMemoryLearningEventPublisher)
        assert isinstance(factory.dataset_exporter, InMemoryDatasetExporter)

    def test_factory_is_reusable(self) -> None:
        """build_all can be called multiple times on the same factory."""
        factory = LearningServiceFactory()
        s1 = factory.build_all()
        s2 = factory.build_all()

        # Same references — factory holds shared instances
        assert s1["decision_service"] is s2["decision_service"]
        assert s1["signal_service"] is s2["signal_service"]
