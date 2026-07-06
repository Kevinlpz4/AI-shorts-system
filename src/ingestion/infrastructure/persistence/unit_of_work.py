"""
SQLAlchemyUnitOfWork — Transaction lifecycle for Ingestion BC persistence.

Owns Session creation, 5-repo sharing, commit/rollback/close,
post-commit domain event collection, and event publication.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from foundation.base.aggregate_root import AggregateRoot
from foundation.events.domain_event import DomainEvent

from ingestion.application.ports.event_publisher import EventPublisher

from ingestion.infrastructure.persistence.exceptions import PersistenceError
from ingestion.infrastructure.persistence.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyFeedRepository,
    SQLAlchemyNewsSourceRepository,
    SQLAlchemyRawArticleRepository,
    SQLAlchemyTopicRepository,
)


class SQLAlchemyUnitOfWork:
    """
    SQLAlchemy-backed Unit of Work.

    Owns Session lifecycle, shares it across 5 repos, manages
    commit/rollback/close, and collects domain events after
    successful commit.

    Accepts optional EventPublisher (if None, publication is skipped).

    Attributes:
        news_sources: NewsSourceRepository (None before __enter__).
        feeds: FeedRepository (None before __enter__).
        raw_articles: RawArticleRepository (None before __enter__).
        categories: CategoryRepository (None before __enter__).
        topics: TopicRepository (None before __enter__).
        _collected_events: Domain events from last successful commit().
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_publisher = event_publisher
        self._session: Session | None = None

        # Idempotent tracking — set ensures same root registered N times
        # appears exactly once during _collect_events().
        self._modified_roots: set[AggregateRoot] = set()
        self._collected_events: list[DomainEvent] = []

        # Repos — None before __enter__
        self.news_sources: SQLAlchemyNewsSourceRepository | None = None
        self.feeds: SQLAlchemyFeedRepository | None = None
        self.raw_articles: SQLAlchemyRawArticleRepository | None = None
        self.categories: SQLAlchemyCategoryRepository | None = None
        self.topics: SQLAlchemyTopicRepository | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def __enter__(self) -> Self:
        """Create Session, init 5 repos with shared Session."""
        self._session = self._session_factory()
        self.news_sources = SQLAlchemyNewsSourceRepository(self._session)
        self.feeds = SQLAlchemyFeedRepository(self._session)
        self.raw_articles = SQLAlchemyRawArticleRepository(self._session)
        self.categories = SQLAlchemyCategoryRepository(self._session)
        self.topics = SQLAlchemyTopicRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Rollback on error, always close. Never swallow exceptions."""
        if exc_type is not None:
            self.rollback()
        self.close()
        # Explicit None return — never swallow the exception
        return None

    # ── Transaction control ───────────────────────────────────────────────

    def commit(self) -> None:
        """Persist changes, collect and publish domain events.

        Publication happens ONLY after successful commit.
        If publish_many() fails the commit is NOT rolled back
        (ADR-025: commit already succeeded).

        Raises:
            PersistenceError: If session.commit() fails (session rolled back),
                or if publish_many() fails (commit NOT rolled back).
        """
        if self._session is None:
            raise PersistenceError("Cannot commit: no active session")

        try:
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise PersistenceError(
                f"Commit failed: {exc}",
            ) from exc

        self._collect_events()

        if self._event_publisher is not None and self._collected_events:
            try:
                self._event_publisher.publish_many(self._collected_events)
            except Exception as exc:
                # ADR-025: commit already done, DO NOT rollback
                raise PersistenceError(
                    "Commit succeeded but event publication failed:"
                    f" {exc}",
                ) from exc
            finally:
                # Always clear after publish attempt — even if it fails
                self._collected_events.clear()

    def rollback(self) -> None:
        """Discard uncommitted changes. Idempotent."""
        if self._session is not None:
            self._session.rollback()

    def close(self) -> None:
        """Close session. Idempotent — safe to call multiple times."""
        if self._session is not None:
            self._session.close()
            self._session = None

    # ── Event collection ──────────────────────────────────────────────────

    def register_modified(self, root: AggregateRoot) -> None:
        """Register an aggregate root as modified for event collection.

        Uses a set internally — registering the same root N times
        is idempotent (appears exactly once during collection).

        Call after repo.save(root) to ensure the root's pending domain
        events are collected on the next commit().
        """
        self._modified_roots.add(root)

    def _collect_events(self) -> None:
        """Pull events from all modified roots. Clears tracking set."""
        for root in self._modified_roots:
            self._collected_events.extend(root.pull_events())
        self._modified_roots.clear()
