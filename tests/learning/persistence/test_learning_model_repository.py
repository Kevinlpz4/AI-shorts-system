"""
Tests for LearningModelRepository — save, find, version ordering.
"""
from __future__ import annotations

import pytest

from learning.domain.entities.ids import LearningModelId
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.persistence.repositories.learning_model_repository import LearningModelRepository
from foundation.result.result import Success, Failure


class TestLearningModelRepositorySave:
    def test_save_and_find_by_id(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)
        session.commit()

        result = repo.find_by_id(model.id)
        assert isinstance(result, Success)
        loaded = result.unwrap()
        assert loaded.id == model.id
        assert loaded.algorithm_version == AlgorithmVersion(major=1, minor=0, patch=0)

    def test_upsert_insert(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)
        session.commit()

        result = repo.find_by_id(model.id)
        assert isinstance(result, Success)

    def test_upsert_update(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)
        session.flush()

        # Update weights
        new_weights = ScoreWeights(
            relevance=0.3, popularity=0.3, recency=0.2, source_reliability=0.2
        )
        model.adjust_weights(new_weights, reason="Testing adjustment")
        repo.save(model)
        session.commit()

        result = repo.find_by_id(model.id)
        loaded = result.unwrap()
        assert loaded.current_weights == new_weights


class TestLearningModelRepositoryFindById:
    def test_find_existing(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model()
        repo.save(model)
        session.commit()

        result = repo.find_by_id(model.id)
        assert isinstance(result, Success)

    def test_find_nonexistent(self, session):
        repo = LearningModelRepository(session)
        result = repo.find_by_id(LearningModelId.generate())
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.MODEL_NOT_FOUND


class TestLearningModelRepositoryFindCurrent:
    def test_find_current(self, session, make_learning_model):
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

        result = repo.find_current()
        assert isinstance(result, Success)
        assert result.unwrap().algorithm_version == AlgorithmVersion(major=2, minor=0, patch=0)

    def test_find_current_with_minor_versions(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        v10 = make_learning_model(
            algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0)
        )
        v11 = make_learning_model(
            algorithm_version=AlgorithmVersion(major=1, minor=1, patch=0)
        )
        v12 = make_learning_model(
            algorithm_version=AlgorithmVersion(major=1, minor=2, patch=0)
        )
        repo.save(v10)
        repo.save(v11)
        repo.save(v12)
        session.commit()

        result = repo.find_current()
        assert isinstance(result, Success)
        assert result.unwrap().algorithm_version == AlgorithmVersion(major=1, minor=2, patch=0)

    def test_find_current_empty(self, session):
        repo = LearningModelRepository(session)
        result = repo.find_current()
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.MODEL_NOT_FOUND


class TestLearningModelRepositoryFindByVersion:
    def test_find_by_version(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model(
            algorithm_version=AlgorithmVersion(major=3, minor=5, patch=2)
        )
        repo.save(model)
        session.commit()

        result = repo.find_by_version("3.5.2")
        assert isinstance(result, Success)
        assert result.unwrap().algorithm_version == AlgorithmVersion(major=3, minor=5, patch=2)

    def test_find_by_version_nonexistent(self, session):
        repo = LearningModelRepository(session)
        result = repo.find_by_version("99.99.99")
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.MODEL_NOT_FOUND


class TestLearningModelRepositoryVersionOrdering:
    def test_version_ordering(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        versions = [
            AlgorithmVersion(major=1, minor=0, patch=0),
            AlgorithmVersion(major=0, minor=9, patch=5),
            AlgorithmVersion(major=1, minor=0, patch=1),
            AlgorithmVersion(major=0, minor=10, patch=0),
        ]
        for v in versions:
            repo.save(make_learning_model(algorithm_version=v))
        session.commit()

        result = repo.find_current()
        assert isinstance(result, Success)
        # 1.0.1 > 1.0.0 > 0.10.0 > 0.9.5
        assert result.unwrap().algorithm_version == AlgorithmVersion(major=1, minor=0, patch=1)

    def test_single_model_is_current(self, session, make_learning_model):
        repo = LearningModelRepository(session)
        model = make_learning_model(
            algorithm_version=AlgorithmVersion(major=0, minor=1, patch=0)
        )
        repo.save(model)
        session.commit()

        result = repo.find_current()
        assert isinstance(result, Success)
        assert result.unwrap().id == model.id
