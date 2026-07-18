"""
Tests for LearningSignalRepository — save, upsert, batch, queries.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.domain.entities.ids import LearningSignalId
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.persistence.repositories.learning_signal_repository import LearningSignalRepository
from foundation.result.result import Success, Failure


class TestLearningSignalRepositorySave:
    def test_save_and_find_by_id(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal()
        repo.save(signal)
        session.commit()

        result = repo.find_by_id(signal.id)
        assert isinstance(result, Success)
        loaded = result.unwrap()
        assert loaded.id == signal.id
        assert loaded.signal_type == SignalType.KEYWORD
        assert loaded.dimension == "python"

    def test_upsert_insert(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal()
        repo.save(signal)
        session.commit()

        found = session.query(
            __import__("learning.persistence.models.learning_signal", fromlist=["LearningSignalModel"]).LearningSignalModel
        ).first()
        assert found.version == 1

    def test_upsert_update(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal()
        repo.save(signal)
        session.flush()

        # Update signal
        signal.update(
            new_sample_size=20,
            new_approval_rate=0.9,
            new_strength=SignalStrength(value=0.9, decay_factor=0.1),
            new_window=TimeWindow(
                start=datetime.now(timezone.utc) - timedelta(days=60),
                end=datetime.now(timezone.utc),
            ),
        )
        repo.save(signal)
        session.commit()

        result = repo.find_by_id(signal.id)
        loaded = result.unwrap()
        assert loaded.sample_size == 20
        assert loaded.approval_rate == 0.9

    def test_save_batch(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signals = [
            make_learning_signal(dimension=f"dim-{i}") for i in range(5)
        ]
        repo.save_batch(signals)
        session.commit()

        for s in signals:
            result = repo.find_by_id(s.id)
            assert isinstance(result, Success)

    def test_save_batch_upsert(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal()
        repo.save(signal)
        session.flush()

        # Batch save with same signal (should update)
        repo.save_batch([signal])
        session.commit()

        result = repo.find_by_id(signal.id)
        assert isinstance(result, Success)


class TestLearningSignalRepositoryFindById:
    def test_find_existing(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal()
        repo.save(signal)
        session.commit()

        result = repo.find_by_id(signal.id)
        assert isinstance(result, Success)

    def test_find_nonexistent(self, session):
        repo = LearningSignalRepository(session)
        result = repo.find_by_id(LearningSignalId.generate())
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.SIGNAL_NOT_FOUND


class TestLearningSignalRepositoryFindByTypeAndDimension:
    def test_find_by_type_and_dimension(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        signal = make_learning_signal(
            signal_type=SignalType.SOURCE, dimension="bbc-news"
        )
        repo.save(signal)
        session.commit()

        result = repo.find_by_type_and_dimension(SignalType.SOURCE, "bbc-news")
        assert isinstance(result, Success)
        assert result.unwrap().id == signal.id

    def test_find_nonexistent_type_dim(self, session):
        repo = LearningSignalRepository(session)
        result = repo.find_by_type_and_dimension(SignalType.SOURCE, "nonexistent")
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.SIGNAL_NOT_FOUND


class TestLearningSignalRepositoryFindByWindow:
    def test_find_by_window(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        now = datetime.now(timezone.utc)
        old = make_learning_signal(
            dimension="old",
            last_updated=now - timedelta(days=30),
        )
        recent = make_learning_signal(
            dimension="recent",
            last_updated=now - timedelta(days=1),
        )
        repo.save(old)
        repo.save(recent)
        session.commit()

        results = repo.find_by_window(
            start=now - timedelta(days=5),
            end=now,
        )
        assert len(results) == 1
        assert results[0].dimension == "recent"

    def test_find_by_window_empty(self, session):
        repo = LearningSignalRepository(session)
        now = datetime.now(timezone.utc)
        results = repo.find_by_window(start=now - timedelta(days=5), end=now)
        assert len(results) == 0


class TestLearningSignalRepositoryFindAllActive:
    def test_find_active_signals(self, session, make_learning_signal):
        repo = LearningSignalRepository(session)
        active = make_learning_signal(dimension="active", sample_size=10)
        inactive = make_learning_signal(dimension="inactive", sample_size=0)
        repo.save(active)
        repo.save(inactive)
        session.commit()

        results = repo.find_all_active()
        assert len(results) == 1
        assert results[0].dimension == "active"

    def test_find_active_empty(self, session):
        repo = LearningSignalRepository(session)
        results = repo.find_all_active()
        assert len(results) == 0
