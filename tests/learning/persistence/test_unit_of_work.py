"""
Tests for SqlAlchemyUnitOfWork — commit, rollback, auto-commit, auto-rollback.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from learning.domain.entities.ids import FeedbackId
from learning.domain.value_objects.decision_type import DecisionType
from learning.persistence.unit_of_work import SqlAlchemyUnitOfWork


class TestUnitOfWorkCommit:
    def test_commit_persists_changes(self, session_factory, make_feedback_record):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            fb = make_feedback_record()
            uow.feedback.save(fb)

        # New session to verify persistence
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            result = uow.feedback.find_by_id(fb.id)
            assert result.is_success

    def test_commit_across_repositories(self, session_factory, make_feedback_record, make_learning_signal):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            fb = make_feedback_record()
            signal = make_learning_signal()
            uow.feedback.save(fb)
            uow.signal.save(signal)

        with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert uow.feedback.find_by_id(fb.id).is_success
            assert uow.signal.find_by_id(signal.id).is_success

    def test_multiple_commits(self, session_factory, make_feedback_record):
        for i in range(3):
            with SqlAlchemyUnitOfWork(session_factory) as uow:
                fb = make_feedback_record(topic_id=f"topic-{i}")
                uow.feedback.save(fb)

        with SqlAlchemyUnitOfWork(session_factory) as uow:
            all_fb = uow.feedback.find_by_topic_id("topic-0")
            assert len(all_fb) == 1


class TestUnitOfWorkRollback:
    def test_rollback_on_exception(self, session_factory, make_feedback_record):
        fb = make_feedback_record()
        try:
            with SqlAlchemyUnitOfWork(session_factory) as uow:
                uow.feedback.save(fb)
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Should NOT be persisted
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            result = uow.feedback.find_by_id(fb.id)
            assert result.is_failure

    def test_explicit_rollback(self, session_factory, make_feedback_record):
        fb = make_feedback_record()
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.feedback.save(fb)
            uow.rollback()

        with SqlAlchemyUnitOfWork(session_factory) as uow:
            result = uow.feedback.find_by_id(fb.id)
            assert result.is_failure


class TestUnitOfWorkAutoCommit:
    def test_auto_commit_on_clean_exit(self, session_factory, make_feedback_record):
        fb = make_feedback_record()
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.feedback.save(fb)
        # __exit__ should auto-commit (no exception)

        with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert uow.feedback.find_by_id(fb.id).is_success


class TestUnitOfWorkAutoRollback:
    def test_auto_rollback_on_exception(self, session_factory, make_feedback_record):
        fb = make_feedback_record()
        with pytest.raises(RuntimeError):
            with SqlAlchemyUnitOfWork(session_factory) as uow:
                uow.feedback.save(fb)
                raise RuntimeError("Boom")

        with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert uow.feedback.find_by_id(fb.id).is_failure


class TestUnitOfWorkPropertyAccessors:
    def test_session_accessor(self, session_factory):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert uow.session is not None

    def test_repositories_accessible(self, session_factory):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert uow.feedback is not None
            assert uow.signal is not None
            assert uow.source_quality is not None
            assert uow.learning_model is not None
            assert uow.knowledge_timeline is not None
            assert uow.feature_store is not None
            assert uow.dataset is not None
            assert uow.artifact is not None

    def test_accessors_fail_before_enter(self, session_factory):
        uow = SqlAlchemyUnitOfWork(session_factory)
        with pytest.raises(AssertionError):
            _ = uow.feedback


class TestUnitOfWorkSessionClose:
    def test_session_identity_map_cleared_after_exit(self, session_factory):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            session = uow.session

        # After __exit__, session close was called — identity map should be empty
        assert len(session.identity_map) == 0
