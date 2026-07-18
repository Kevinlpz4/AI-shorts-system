"""
Shared fixtures for Learning Intelligence API presentation tests.

Provides TestClient, real LearningServiceFactory, and dependency overrides.
Seeds a default LearningModel and common source profiles so services work.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

import pytest
from fastapi.testclient import TestClient

from learning.domain.entities.ids import LearningModelId, SourceQualityId
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.infrastructure.composition import LearningServiceFactory
from learning.presentation.app import create_app
from learning.presentation.dependencies import ServiceDependencies, get_services


def _seed_factory(factory: LearningServiceFactory) -> None:
    """Seed the factory's repos with default data for testing.

    - Creates a default LearningModel (required by prediction/explanation/recommendation).
    - Creates common SourceQualityProfile entries (updated by DecisionService on feedback).
    """
    # Seed a default LearningModel
    model = LearningModel(
        id=LearningModelId.generate(),
        algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
        current_weights=ScoreWeights(
            relevance=0.30,
            popularity=0.25,
            recency=0.20,
            source_reliability=0.25,
        ),
        minimum_confidence=0.5,
        minimum_sample_size=10,
        active_rules=[],
    )
    factory.model_repo.save(model)

    # Seed common source profiles so DecisionService can update them
    # and source-quality lookup works after feedback.
    common_sources = [
        "reuters",
        "bbc",
        "techcrunch",
        "tested_source",
        "schema_test_source",
        "rate_test_source",
        "conf_test_source",
        "kw_test_source",
        "trend_test_source",
        "count_test_source",
        "knowledge_test_source",
        "analytics_test_source",
    ]
    for name in common_sources:
        profile = SourceQualityProfile(
            id=SourceQualityId.generate(),
            source_name=name,
            total_decisions=0,
            approved_count=0,
            rejected_count=0,
            auto_approved_count=0,
            auto_rejected_count=0,
            overridden_count=0,
        )
        factory.source_quality_repo.save(profile)


@pytest.fixture()
def factory() -> LearningServiceFactory:
    """Create a real LearningServiceFactory, seeded with default data."""
    f = LearningServiceFactory()
    _seed_factory(f)
    return f


@pytest.fixture()
def app(factory: LearningServiceFactory):
    """Create a FastAPI app with real service dependencies."""
    _app = create_app()

    async def override_services() -> ServiceDependencies:
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
            timeline_storage=None,
            dataset_repository=None,
            artifact_repo=None,
        )

    _app.dependency_overrides[get_services] = override_services
    return _app


@pytest.fixture()
def client(app) -> TestClient:
    """Create a TestClient with the configured app."""
    return TestClient(app, raise_server_exceptions=False)
