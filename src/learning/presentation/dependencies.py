"""
Service dependency injection for the Learning Intelligence API.

Provides a centralized ServiceDependencies dataclass that all routers
use to access application services and repositories.
"""
from __future__ import annotations

from dataclasses import dataclass

from learning.infrastructure.composition import LearningServiceFactory
from learning.infrastructure.knowledge_storage import KnowledgeTimelineStorage

_factory: LearningServiceFactory | None = None


def get_factory() -> LearningServiceFactory:
    """Get or create the singleton LearningServiceFactory."""
    global _factory
    if _factory is None:
        _factory = LearningServiceFactory()
    return _factory


@dataclass
class ServiceDependencies:
    """Centralized service dependencies for all routers.

    Holds references to all application services and repositories
    needed by the presentation layer.
    """

    prediction_service: object
    explanation_service: object
    recommendation_service: object
    decision_service: object
    analytics_service: object
    source_quality_repo: object
    signal_repo: object
    model_repo: object
    feedback_repo: object
    timeline_storage: KnowledgeTimelineStorage | None
    dataset_repository: object | None
    artifact_repo: object | None


async def get_services() -> ServiceDependencies:
    """FastAPI dependency that provides all service instances.

    Builds dependencies from the LearningServiceFactory composition root.
    """
    factory = get_factory()
    return ServiceDependencies(
        prediction_service=factory.prediction_service,
        explanation_service=factory.explanation_service,
        recommendation_service=factory.recommendation_service,
        decision_service=factory.decision_service,
        analytics_service=factory.analytics_service,
        source_quality_repo=factory.source_quality_repo,
        signal_repo=factory.signal_repo,
        model_repo=factory.model_repo,
        feedback_repo=factory.feedback_repo,
        timeline_storage=KnowledgeTimelineStorage(),
        dataset_repository=None,  # Would use persistence in production
        artifact_repo=None,  # Would use persistence in production
    )
