"""Tests for SQLAlchemyEventPublisher — in-memory event publication.

Covers:
    - Unit: SQLAlchemyEventPublisher.publish() and publish_many()
    - Integration: UoW + EventPublisher — post-commit publication flow
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from foundation.base.aggregate_root import AggregateRoot
from foundation.events.domain_event import DomainEvent
from ingestion.infrastructure.event_publisher import SQLAlchemyEventPublisher
from ingestion.infrastructure.persistence.exceptions import PersistenceError


# ══════════════════════════════════════════════════════════════════════════════
# Unit: SQLAlchemyEventPublisher
# ══════════════════════════════════════════════════════════════════════════════


class TestSQLAlchemyEventPublisher:
    """R11: SQLAlchemyEventPublisher — in-memory event publication."""

    def test_publish_stores_single_event(self):
        """R11.#23: publish() MUST store the event in events list."""
        publisher = SQLAlchemyEventPublisher()
        event = MagicMock(spec=DomainEvent)

        publisher.publish(event)

        assert len(publisher.events) == 1
        assert publisher.events[0] is event

    def test_publish_many_stores_multiple_events(self):
        """R11.#24: publish_many() MUST store all events."""
        publisher = SQLAlchemyEventPublisher()
        events = [MagicMock(spec=DomainEvent) for _ in range(3)]

        publisher.publish_many(events)

        assert len(publisher.events) == 3
        assert all(a is b for a, b in zip(publisher.events, events))

    def test_publish_many_preserves_order(self):
        """R13.#26: publish_many() MUST preserve insertion order."""
        publisher = SQLAlchemyEventPublisher()
        event_a = MagicMock(spec=DomainEvent)
        event_b = MagicMock(spec=DomainEvent)
        event_c = MagicMock(spec=DomainEvent)

        publisher.publish_many([event_a, event_b, event_c])

        assert publisher.events[0] is event_a
        assert publisher.events[1] is event_b
        assert publisher.events[2] is event_c

    def test_publish_many_empty_list(self):
        """publish_many([]) MUST NOT error and events stays empty."""
        publisher = SQLAlchemyEventPublisher()

        publisher.publish_many([])

        assert len(publisher.events) == 0

    def test_publisher_events_property_is_observable(self):
        """events property MUST expose all stored events."""
        publisher = SQLAlchemyEventPublisher()
        event = MagicMock(spec=DomainEvent)

        publisher.publish(event)

        assert publisher.events == [event]


# ══════════════════════════════════════════════════════════════════════════════
# Integration: UoW + EventPublisher
# ══════════════════════════════════════════════════════════════════════════════


class TestUnitOfWorkEventPublication:
    """R2/R12/R14: UoW commit() integration with EventPublisher."""

    def test_commit_publishes_collected_events(self, uow):
        """R2.#28: register_modified + commit -> publisher receives events."""
        publisher = SQLAlchemyEventPublisher()
        uow._event_publisher = publisher

        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        assert len(publisher.events) == 1
        assert publisher.events[0] is event

    def test_commit_without_publisher_skips_publication(self, uow):
        """R2.#29: UoW without event_publisher -> publication skipped."""
        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        # No publisher set — no crash, no events published
        # (default is None, which skips publication)

    def test_commit_failure_does_not_publish(self, uow):
        """R2: commit fails -> publisher MUST NOT be called."""
        from sqlalchemy.exc import IntegrityError

        publisher = SQLAlchemyEventPublisher()
        uow._event_publisher = publisher

        with uow:
            uow._session.commit = MagicMock(  # type: ignore[method-assign]
                side_effect=IntegrityError("stmt", "params", "orig"),
            )
            with pytest.raises(PersistenceError):
                uow.commit()

        assert len(publisher.events) == 0

    def test_publish_failure_does_not_rollback(self, uow):
        """R12.#25: publish_many fails -> commit NOT rolled back,
        PersistenceError propagated."""
        publisher = SQLAlchemyEventPublisher()
        publisher.publish_many = MagicMock(
            side_effect=RuntimeError("publish failed"),
        )
        uow._event_publisher = publisher

        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]
        commit_mock = MagicMock()

        with uow:
            uow.register_modified(root)
            uow._session.commit = commit_mock  # type: ignore[method-assign]
            with pytest.raises(PersistenceError, match="event publication failed"):
                uow.commit()

        # Commit was NOT rolled back (no rollback call after publish failure)
        commit_mock.assert_called_once()

    def test_commit_twice_without_changes(self, uow):
        """R14.#27: Second commit without modifications -> 0 new events."""
        publisher = SQLAlchemyEventPublisher()
        uow._event_publisher = publisher

        event = MagicMock(spec=DomainEvent)
        root = MagicMock(spec=AggregateRoot)
        root.pull_events.return_value = [event]

        with uow:
            # First commit
            uow.register_modified(root)
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

            # Second commit — no new modifications
            uow._session.commit = MagicMock()  # type: ignore[method-assign]
            uow.commit()

        # Only 1 event from first commit
        assert len(publisher.events) == 1
