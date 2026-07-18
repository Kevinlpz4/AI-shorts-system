"""
Tests for optimistic locking / version conflict detection.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from learning.domain.entities.ids import FeedbackId, LearningSignalId
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.persistence.models.base import Base
from learning.persistence.models.feedback import FeedbackRecordModel
from learning.persistence.models.learning_signal import LearningSignalModel
from learning.persistence.repositories.feedback_repository import FeedbackRepository
from learning.persistence.repositories.learning_signal_repository import LearningSignalRepository
from learning.persistence.mappers.feedback_mapper import FeedbackRecordMapper
from learning.persistence.mappers.learning_signal_mapper import LearningSignalMapper
from datetime import datetime, timedelta, timezone


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine)


class TestFeedbackRepositoryVersionConflict:
    def test_duplicate_save_raises(self, session_factory, make_feedback_record):
        """Saving same FeedbackRecord twice raises ValueError."""
        fb = make_feedback_record()

        with session_factory() as s1:
            repo = FeedbackRepository(s1)
            repo.save(fb)
            s1.commit()

        with session_factory() as s2:
            repo = FeedbackRepository(s2)
            with pytest.raises(ValueError, match="already exists"):
                repo.save(fb)


class TestLearningSignalVersionIncrement:
    def test_version_increments_on_update(self, session_factory, make_learning_signal):
        """Version should increment on each save (upsert)."""
        signal = make_learning_signal()

        with session_factory() as s1:
            repo = LearningSignalRepository(s1)
            repo.save(signal)
            s1.commit()

        # Update and save again
        signal.update(
            new_sample_size=20,
            new_approval_rate=0.9,
            new_strength=SignalStrength(value=0.9, decay_factor=0.1),
            new_window=TimeWindow(
                start=datetime.now(timezone.utc) - timedelta(days=30),
                end=datetime.now(timezone.utc),
            ),
        )

        with session_factory() as s2:
            repo = LearningSignalRepository(s2)
            repo.save(signal)
            s2.commit()

            # Check version incremented
            model = (
                s2.query(LearningSignalModel)
                .filter(LearningSignalModel.id == str(signal.id))
                .first()
            )
            assert model.version == 2

    def test_version_starts_at_1(self, session_factory, make_learning_signal):
        """New records should have version=1."""
        signal = make_learning_signal()

        with session_factory() as s:
            repo = LearningSignalRepository(s)
            repo.save(signal)
            s.commit()

            model = (
                s.query(LearningSignalModel)
                .filter(LearningSignalModel.id == str(signal.id))
                .first()
            )
            assert model.version == 1


class TestSourceQualityVersionIncrement:
    def test_version_increments(self, session_factory, make_source_quality):
        """Source quality profile version increments on upsert."""
        profile = make_source_quality()

        with session_factory() as s1:
            repo = __import__(
                "learning.persistence.repositories.source_quality_repository",
                fromlist=["SourceQualityRepository"],
            ).SourceQualityRepository(s1)
            repo.save(profile)
            s1.commit()

        profile.record_decision("approved")

        with session_factory() as s2:
            from learning.persistence.repositories.source_quality_repository import SourceQualityRepository
            repo = SourceQualityRepository(s2)
            repo.save(profile)
            s2.commit()

            from learning.persistence.models.source_quality import SourceQualityProfileModel
            model = (
                s2.query(SourceQualityProfileModel)
                .filter(SourceQualityProfileModel.source_name == profile.source_name)
                .first()
            )
            assert model.version == 2
