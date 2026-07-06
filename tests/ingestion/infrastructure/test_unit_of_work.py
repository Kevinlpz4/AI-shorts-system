"""
Tests for SQLAlchemyUnitOfWork — Session lifecycle, commit/rollback/close,
event collection, shared Session identity.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from foundation.base.aggregate_root import AggregateRoot
from foundation.events.domain_event import DomainEvent

from ingestion.infrastructure.persistence import SQLAlchemyUnitOfWork
from ingestion.infrastructure.persistence.exceptions import PersistenceError


class TestUnitOfWorkCreation:
    """R1: UoW Creation — repos None before __enter__, initialized after."""

    def test_uow_repos_are_none_before_enter(self, uow):
        """R1.#1: Repos MUST be None before __enter__ is called."""
        assert uow.news_sources is None
        assert uow.feeds is None
        assert uow.raw_articles is None
        assert uow.categories is None
        assert uow.topics is None

    def test_uow_creates_session_and_repos_on_enter(self, uow):
        """R1.#2: __enter__ MUST create Session and init all 5 repos."""
        with uow:
            assert uow.news_sources is not None
            assert uow.feeds is not None
            assert uow.raw_articles is not None
            assert uow.categories is not None
            assert uow.topics is not None
            # Session is alive
            assert uow._session is not None


class TestUnitOfWorkCommit:
    """R2: Commit lifecycle — exactly once, event collection, failure."""

    def test_commit_calls_session_commit_once(self, uow):
        """R2.#3: commit() MUST call session.commit() exactly once."""
        with uow:
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()
            uow._session.commit.assert_called_once()

    def test_commit_collects_events(self, uow):
        """R2.#4: commit() MUST collect events from registered roots."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        assert len(uow._collected_events) == 1
        assert uow._collected_events[0] is event

    def test_commit_failure_raises_persistence_error(self, uow):
        """R2.#5: When commit fails, MUST raise PersistenceError."""
        with uow:
            uow._session.commit = MagicMock(  # type: ignore[method-assign]
                side_effect=IntegrityError("stmt", "params", "orig"),
            )
            with pytest.raises(PersistenceError, match="Commit failed"):
                uow.commit()


class TestUnitOfWorkRollback:
    """R3: Rollback lifecycle — explicit and auto on exception."""

    def test_explicit_rollback(self, uow):
        """R3.#6: rollback() MUST call session.rollback()."""
        with uow:
            uow._session.rollback = MagicMock()  # type: ignore[method-assign]
            uow.rollback()
            uow._session.rollback.assert_called_once()

    def test_auto_rollback_on_exception(self, uow):
        """R3.#7: __exit__ MUST call rollback() when an exception occurs."""
        rollback_spy = None
        try:
            with uow:
                uow._session.rollback = MagicMock()  # type: ignore[method-assign]
                rollback_spy = uow._session.rollback
                raise ValueError("boom")
        except ValueError:
            pass

        assert rollback_spy is not None
        rollback_spy.assert_called_once()


class TestUnitOfWorkClose:
    """R4: Close lifecycle — normal exit, error exit, idempotent."""

    def test_close_called_on_normal_exit(self, uow):
        """R4.#8: __exit__ MUST call session.close() when no exception."""
        mock_close = MagicMock()
        with uow:
            uow._session.close = mock_close  # type: ignore[method-assign]

        # _session is None after close(), so we verify via the captured mock
        mock_close.assert_called_once()

    def test_close_called_on_error_exit(self, uow):
        """R4.#9: __exit__ MUST call session.close() even on exception."""
        mock_close = MagicMock()
        try:
            with uow:
                uow._session.close = mock_close  # type: ignore[method-assign]
                raise ValueError("boom")
        except ValueError:
            pass

        # _session is None after close(), so we verify via the captured mock
        mock_close.assert_called_once()

    def test_close_idempotent(self, uow):
        """R4.#10: close() MUST be idempotent — second call no error."""
        with uow:
            pass  # __exit__ calls close() once
        # _session is now None — calling close() again must be safe
        uow.close()  # second call — must not raise


class TestUnitOfWorkContextManager:
    """R5: Context manager — basic usage and nested independence."""

    def test_basic_with_statement(self, uow):
        """R5.#11: UoW MUST work as context manager with accessible repos."""
        with uow:
            assert uow._session is not None
            assert uow.news_sources is not None
            # Session is active and can execute queries
            from sqlalchemy import text

            result = uow._session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # After exit, session is closed
        assert uow._session is None

    def test_nested_uows_have_independent_sessions(
        self, sqlite_session_factory, tables,
    ):
        """R5.#12: Each UoW instance MUST manage its own Session."""
        uow1 = SQLAlchemyUnitOfWork(sqlite_session_factory)
        uow2 = SQLAlchemyUnitOfWork(sqlite_session_factory)

        with uow1:
            with uow2:
                assert uow1._session is not uow2._session
                assert uow1._session is not None
                assert uow2._session is not None

            # uow2 exited — its session is closed
            assert uow2._session is None
            # uow1 still alive
            assert uow1._session is not None

        # uow1 exited — its session is closed
        assert uow1._session is None


class TestUnitOfWorkSessionIdentity:
    """R6/R9: Cross-repo Session sharing and identity chain."""

    def test_all_repos_share_same_session(self, uow):
        """R6.#13: All 5 repos MUST share the exact same Session."""
        with uow:
            s = uow.news_sources._session
            assert s is uow.feeds._session
            assert s is uow.raw_articles._session
            assert s is uow.categories._session
            assert s is uow.topics._session

    def test_session_identity_chain(self, uow):
        """R9.#14: Identity chain across ALL 5 repos — same Session object.

        This is the fundamental purpose of the Unit of Work:
        a single transaction identity across all repositories.
        """
        with uow:
            s = uow.news_sources._session
            assert s is uow.feeds._session
            assert s is uow.raw_articles._session
            assert s is uow.categories._session
            assert s is uow.topics._session


class TestUnitOfWorkEventCollection:
    """R7: Event collection — post-commit, no-commit, rollback, multi, idempotent."""

    def test_events_collected_after_commit(self, uow):
        """R7.#15: Events MUST be in _collected_events after commit()."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        assert len(uow._collected_events) == 1
        assert uow._collected_events[0] is event

    def test_no_events_without_commit(self, uow):
        """R7.#16: _collected_events MUST be empty if commit() not called."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            # No commit() called

        assert len(uow._collected_events) == 0

    def test_no_events_after_rollback(self, uow):
        """R7.#17: _collected_events MUST be empty after rollback()."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            uow.rollback()

        assert len(uow._collected_events) == 0

    def test_events_from_multiple_roots(self, uow):
        """R7.#18: Events from ALL registered roots MUST be collected."""
        event1 = MagicMock(spec=DomainEvent)
        event2 = MagicMock(spec=DomainEvent)
        root1 = MagicMock(spec=AggregateRoot)
        root1.pull_events.return_value = [event1]
        root2 = MagicMock(spec=AggregateRoot)
        root2.pull_events.return_value = [event2]

        with uow:
            uow.register_modified(root1)
            uow.register_modified(root2)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        assert len(uow._collected_events) == 2
        assert event1 in uow._collected_events
        assert event2 in uow._collected_events

    def test_register_modified_is_idempotent(self, uow):
        """R7.#19: Same root registered 5 times → appears exactly once."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            # Register same root 5 times
            uow.register_modified(root)
            uow.register_modified(root)
            uow.register_modified(root)
            uow.register_modified(root)
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        # pull_events called exactly once (not 5 times)
        root.pull_events.assert_called_once()
        assert len(uow._collected_events) == 1
