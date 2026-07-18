"""
Tests for version tracking — version increment, reproducibility queries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.domain.entities.ids import LearningModelId
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.persistence.repositories.learning_model_repository import LearningModelRepository


class TestVersionTracking:
    def test_version_increment_on_update(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)
        session.flush()

        # Update weights
        new_weights = ScoreWeights(
            relevance=0.3, popularity=0.3, recency=0.2, source_reliability=0.2
        )
        model.adjust_weights(new_weights, reason="Testing")
        repo.save(model)
        session.commit()

        from learning.persistence.models.learning_model import LearningModelModel
        db_model = (
            session.query(LearningModelModel)
            .filter(LearningModelModel.id == str(model.id))
            .first()
        )
        assert db_model.version == 2

    def test_multiple_updates_increment_version(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)

        for i in range(5):
            weights = ScoreWeights(
                relevance=0.25 + i * 0.01,
                popularity=0.25 - i * 0.01,
                recency=0.25,
                source_reliability=0.25,
            )
            model.adjust_weights(weights, reason=f"Update {i}")
            repo.save(model)
        session.commit()

        from learning.persistence.models.learning_model import LearningModelModel
        db_model = (
            session.query(LearningModelModel)
            .filter(LearningModelModel.id == str(model.id))
            .first()
        )
        assert db_model.version == 6  # 1 initial + 5 updates

    def test_version_preserved_after_restart(self, session_factory, make_learning_model):
        """Simulates a 'restart' by creating a new session."""
        model = make_learning_model()

        with session_factory() as s:
            repo = LearningModelRepository(s)
            repo.save(model)
            s.commit()

        # Simulate restart — new session
        with session_factory() as s:
            repo = LearningModelRepository(s)
            result = repo.find_by_id(model.id)
            assert result.is_success
            loaded = result.unwrap()

            # Version should be 1
            loaded.adjust_weights(
                ScoreWeights(
                    relevance=0.3, popularity=0.3, recency=0.2, source_reliability=0.2
                ),
                reason="After restart",
            )
            repo.save(loaded)
            s.commit()

        # Verify version is now 2
        with session_factory() as s:
            from learning.persistence.models.learning_model import LearningModelModel
            db_model = (
                s.query(LearningModelModel)
                .filter(LearningModelModel.id == str(model.id))
                .first()
            )
            assert db_model.version == 2

    def test_algorithm_version_immutability(self, session, make_learning_model):
        """Algorithm version string is stored and retrieved correctly."""
        repo = LearningModelRepository(session)
        model = make_learning_model(
            algorithm_version=AlgorithmVersion(major=3, minor=7, patch=2)
        )
        repo.save(model)
        session.commit()

        from learning.persistence.models.learning_model import LearningModelModel
        db_model = (
            session.query(LearningModelModel)
            .filter(LearningModelModel.id == str(model.id))
            .first()
        )
        assert db_model.algorithm_version_str == "3.7.2"

    def test_find_by_version_reproducibility(self, session, make_learning_model):
        """Can find a specific version for reproducibility."""
        repo = LearningModelRepository(session)
        v1 = make_learning_model(
            algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0)
        )
        v2 = make_learning_model(
            algorithm_version=AlgorithmVersion(major=2, minor=0, patch=0)
        )
        repo.save(v1)
        repo.save(v2)
        session.commit()

        # Find specific version
        result_v1 = repo.find_by_version("1.0.0")
        result_v2 = repo.find_by_version("2.0.0")
        assert result_v1.is_success
        assert result_v2.is_success
        assert result_v1.unwrap().algorithm_version == AlgorithmVersion(major=1, minor=0, patch=0)
        assert result_v2.unwrap().algorithm_version == AlgorithmVersion(major=2, minor=0, patch=0)

    def test_all_versions_listed(self, session, make_learning_model):
        """All saved versions can be found."""
        repo = LearningModelRepository(session)
        versions = [
            AlgorithmVersion(major=1, minor=0, patch=0),
            AlgorithmVersion(major=1, minor=1, patch=0),
            AlgorithmVersion(major=2, minor=0, patch=0),
        ]
        for v in versions:
            repo.save(make_learning_model(algorithm_version=v))
        session.commit()

        for v in versions:
            result = repo.find_by_version(str(v))
            assert result.is_success
