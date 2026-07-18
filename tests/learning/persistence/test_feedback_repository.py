"""
Tests for FeedbackRepository — roundtrip, contract, immutability guarantees.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from learning.domain.entities.ids import FeedbackId
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.value_objects.decision_type import DecisionType
from learning.persistence.repositories.feedback_repository import FeedbackRepository
from foundation.result.result import Success, Failure


class TestFeedbackRepositorySave:
    def test_save_and_find_by_id(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        feedback = make_feedback_record()
        repo.save(feedback)
        session.commit()

        result = repo.find_by_id(feedback.id)
        assert isinstance(result, Success)
        assert result.unwrap().id == feedback.id

    def test_duplicate_id_raises_error(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        feedback = make_feedback_record()
        repo.save(feedback)
        session.flush()

        with pytest.raises(ValueError, match="already exists"):
            repo.save(feedback)

    def test_save_multiple(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        ids = []
        for i in range(5):
            fb = make_feedback_record(topic_id=f"topic-{i}")
            repo.save(fb)
            ids.append(fb.id)
        session.commit()

        for fid in ids:
            result = repo.find_by_id(fid)
            assert isinstance(result, Success)

    def test_save_preserves_all_fields(self, session, make_feedback_record, make_feature_snapshot):
        repo = FeedbackRepository(session)
        snap = make_feature_snapshot(base_score=0.99)
        fb = make_feedback_record(
            topic_id="special-topic",
            decision=DecisionType.REJECTED,
            reason="Low quality content",
            feature_snapshot=snap,
            source_name="bbc-news",
            title="Breaking News",
            score_snapshot={"relevance": 0.1, "popularity": 0.9},
        )
        repo.save(fb)
        session.commit()

        result = repo.find_by_id(fb.id)
        loaded = result.unwrap()
        assert loaded.topic_id == "special-topic"
        assert loaded.decision == DecisionType.REJECTED
        assert loaded.reason == "Low quality content"
        assert loaded.feature_snapshot.base_score == 0.99
        assert loaded.source_name == "bbc-news"
        assert loaded.title == "Breaking News"
        assert loaded.score_snapshot == {"relevance": 0.1, "popularity": 0.9}

    def test_save_rejection_with_reason(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        fb = make_feedback_record(
            decision=DecisionType.AUTO_REJECTED,
            reason="Confidence too low",
        )
        repo.save(fb)
        session.commit()

        result = repo.find_by_id(fb.id)
        assert result.unwrap().reason == "Confidence too low"


class TestFeedbackRepositoryFindById:
    def test_find_existing(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        fb = make_feedback_record()
        repo.save(fb)
        session.commit()

        result = repo.find_by_id(fb.id)
        assert isinstance(result, Success)

    def test_find_nonexistent(self, session):
        repo = FeedbackRepository(session)
        result = repo.find_by_id(FeedbackId.generate())
        assert isinstance(result, Failure)
        assert result.error.code == LearningErrorCode.FEEDBACK_NOT_FOUND


class TestFeedbackRepositoryFindByTopic:
    def test_find_by_topic(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        for i in range(3):
            repo.save(make_feedback_record(topic_id="my-topic"))
        repo.save(make_feedback_record(topic_id="other-topic"))
        session.commit()

        results = repo.find_by_topic_id("my-topic")
        assert len(results) == 3

    def test_find_by_topic_empty(self, session):
        repo = FeedbackRepository(session)
        results = repo.find_by_topic_id("nonexistent")
        assert len(results) == 0


class TestFeedbackRepositoryFindBySource:
    def test_find_by_source(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        repo.save(make_feedback_record(source_name="bbc"))
        repo.save(make_feedback_record(source_name="bbc"))
        repo.save(make_feedback_record(source_name="cnn"))
        session.commit()

        results = repo.find_by_source("bbc")
        assert len(results) == 2

    def test_find_by_source_empty(self, session):
        repo = FeedbackRepository(session)
        results = repo.find_by_source("nonexistent")
        assert len(results) == 0


class TestFeedbackRepositoryFindInWindow:
    def test_find_in_window(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        now = datetime.now(timezone.utc)
        old = make_feedback_record(captured_at=now - timedelta(days=10))
        recent = make_feedback_record(captured_at=now - timedelta(days=1))
        future = make_feedback_record(captured_at=now + timedelta(days=10))
        repo.save(old)
        repo.save(recent)
        repo.save(future)
        session.commit()

        results = repo.find_all_in_window(
            start=now - timedelta(days=5),
            end=now,
        )
        assert len(results) == 1

    def test_find_in_window_empty(self, session):
        repo = FeedbackRepository(session)
        now = datetime.now(timezone.utc)
        results = repo.find_all_in_window(
            start=now - timedelta(days=5),
            end=now,
        )
        assert len(results) == 0


class TestFeedbackRepositoryCountByDecision:
    def test_count_by_decision(self, session, make_feedback_record):
        repo = FeedbackRepository(session)
        repo.save(make_feedback_record(decision=DecisionType.APPROVED))
        repo.save(make_feedback_record(decision=DecisionType.APPROVED))
        repo.save(make_feedback_record(
            decision=DecisionType.REJECTED, reason="bad"
        ))
        session.commit()

        assert repo.count_by_decision(DecisionType.APPROVED) == 2
        assert repo.count_by_decision(DecisionType.REJECTED) == 1
        assert repo.count_by_decision(DecisionType.OVERRIDDEN) == 0

    def test_count_empty(self, session):
        repo = FeedbackRepository(session)
        assert repo.count_by_decision(DecisionType.APPROVED) == 0
