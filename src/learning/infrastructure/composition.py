"""
Composition Root for the Learning Bounded Context.

Wires all Learning BC services with their dependencies using
constructor injection. No IoC container. No service locator.
No global state.

Usage::

    # Production (defaults to LearningSystemClock)
    factory = LearningServiceFactory()
    services = factory.build_all()

    # With custom clock (e.g., frozen for testing)
    clock = LearningFrozenClock(datetime(2026, 7, 15, tzinfo=timezone.utc))
    factory = LearningServiceFactory(clock=clock)
    services = factory.build_all()
"""
from __future__ import annotations

from foundation.ports.clock import ClockPort

from learning.infrastructure.inmemory.clock import LearningSystemClock
from learning.infrastructure.inmemory.dataset_exporter import (
    InMemoryDatasetExporter,
)
from learning.infrastructure.inmemory.event_publisher import (
    InMemoryLearningEventPublisher,
)
from learning.infrastructure.inmemory.repositories import (
    InMemoryFeedbackRepository,
    InMemoryLearningModelRepository,
    InMemoryLearningSignalRepository,
    InMemorySourceQualityRepository,
)
from learning.infrastructure.inmemory.unit_of_work import (
    InMemoryLearningUnitOfWork,
)
from learning.application.services.analytics_service import AnalyticsService
from learning.application.services.dataset_service import DatasetService
from learning.application.services.decision_service import DecisionService
from learning.application.services.explanation_service import ExplanationService
from learning.application.services.prediction_service import PredictionService
from learning.application.services.recommendation_service import (
    RecommendationService,
)
from learning.application.services.scoring_service import ScoringService
from learning.application.services.signal_service import SignalService
from learning.domain.signals.registry import SignalRegistry


class LearningServiceFactory:
    """Composition Root -- wires all Learning BC services.

    Builds all services with their dependencies using constructor injection.
    No global state. No service locator.

    Args:
        clock: Optional clock implementation. Defaults to ``LearningSystemClock``.
            Pass a ``LearningFrozenClock`` for deterministic testing.
    """

    def __init__(self, clock: ClockPort | None = None) -> None:
        self._clock = clock or LearningSystemClock()

        # -- Repositories (InMemory) --
        self._feedback_repo = InMemoryFeedbackRepository()
        self._signal_repo = InMemoryLearningSignalRepository()
        self._source_quality_repo = InMemorySourceQualityRepository()
        self._model_repo = InMemoryLearningModelRepository()

        # -- Application Ports (InMemory) --
        self._uow = InMemoryLearningUnitOfWork()
        self._event_publisher = InMemoryLearningEventPublisher()
        self._dataset_exporter = InMemoryDatasetExporter()

        # -- Domain --
        self._signal_registry = SignalRegistry()

        # -- Services (built with shared dependencies) --
        self._decision_service = DecisionService(
            feedback_repo=self._feedback_repo,
            source_quality_repo=self._source_quality_repo,
            uow=self._uow,
            event_publisher=self._event_publisher,
            clock=self._clock,
        )

        self._signal_service = SignalService(
            signal_repo=self._signal_repo,
            signal_registry=self._signal_registry,
            uow=self._uow,
            event_publisher=self._event_publisher,
            clock=self._clock,
        )

        self._scoring_service = ScoringService(
            model_repo=self._model_repo,
            uow=self._uow,
            event_publisher=self._event_publisher,
            clock=self._clock,
        )

        self._dataset_service = DatasetService(
            feedback_repo=self._feedback_repo,
            source_quality_repo=self._source_quality_repo,
            dataset_exporter=self._dataset_exporter,
            uow=self._uow,
            event_publisher=self._event_publisher,
            clock=self._clock,
        )

        self._analytics_service = AnalyticsService(
            feedback_repo=self._feedback_repo,
            signal_repo=self._signal_repo,
            source_quality_repo=self._source_quality_repo,
        )

        self._prediction_service = PredictionService(
            model_repo=self._model_repo,
            source_quality_repo=self._source_quality_repo,
            signal_repo=self._signal_repo,
        )

        self._explanation_service = ExplanationService(
            model_repo=self._model_repo,
            source_quality_repo=self._source_quality_repo,
            signal_repo=self._signal_repo,
        )

        self._recommendation_service = RecommendationService(
            prediction_service=self._prediction_service,
            explanation_service=self._explanation_service,
            source_quality_repo=self._source_quality_repo,
            model_repo=self._model_repo,
        )

    # -- Service Accessors --

    @property
    def decision_service(self) -> DecisionService:
        """DecisionService instance."""
        return self._decision_service

    @property
    def signal_service(self) -> SignalService:
        """SignalService instance."""
        return self._signal_service

    @property
    def scoring_service(self) -> ScoringService:
        """ScoringService instance."""
        return self._scoring_service

    @property
    def dataset_service(self) -> DatasetService:
        """DatasetService instance."""
        return self._dataset_service

    @property
    def analytics_service(self) -> AnalyticsService:
        """AnalyticsService instance."""
        return self._analytics_service

    @property
    def prediction_service(self) -> PredictionService:
        """PredictionService instance."""
        return self._prediction_service

    @property
    def explanation_service(self) -> ExplanationService:
        """ExplanationService instance."""
        return self._explanation_service

    @property
    def recommendation_service(self) -> RecommendationService:
        """RecommendationService instance."""
        return self._recommendation_service

    # -- Infrastructure Accessors (useful for test setup/assertions) --

    @property
    def feedback_repo(self) -> InMemoryFeedbackRepository:
        """InMemoryFeedbackRepository -- useful for test setup."""
        return self._feedback_repo

    @property
    def signal_repo(self) -> InMemoryLearningSignalRepository:
        """InMemoryLearningSignalRepository -- useful for test setup."""
        return self._signal_repo

    @property
    def source_quality_repo(self) -> InMemorySourceQualityRepository:
        """InMemorySourceQualityRepository -- useful for test setup."""
        return self._source_quality_repo

    @property
    def model_repo(self) -> InMemoryLearningModelRepository:
        """InMemoryLearningModelRepository -- useful for test setup."""
        return self._model_repo

    @property
    def uow(self) -> InMemoryLearningUnitOfWork:
        """InMemoryLearningUnitOfWork -- useful for test assertions."""
        return self._uow

    @property
    def event_publisher(self) -> InMemoryLearningEventPublisher:
        """InMemoryLearningEventPublisher -- useful for test assertions."""
        return self._event_publisher

    @property
    def dataset_exporter(self) -> InMemoryDatasetExporter:
        """InMemoryDatasetExporter -- useful for test assertions."""
        return self._dataset_exporter

    @property
    def clock(self) -> ClockPort:
        """The clock instance used by all services."""
        return self._clock

    def build_all(self) -> dict[str, object]:
        """Build and return a dictionary of all services.

        Returns:
            Dictionary with string keys mapping to service instances.
            Keys: decision_service, signal_service, scoring_service,
            dataset_service, analytics_service, prediction_service,
            explanation_service, recommendation_service.
        """
        return {
            "decision_service": self._decision_service,
            "signal_service": self._signal_service,
            "scoring_service": self._scoring_service,
            "dataset_service": self._dataset_service,
            "analytics_service": self._analytics_service,
            "prediction_service": self._prediction_service,
            "explanation_service": self._explanation_service,
            "recommendation_service": self._recommendation_service,
        }
