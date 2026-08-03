# Design: Sprint 5.4A — SQLAlchemyUnitOfWork + Session Lifecycle

## Technical Approach

Implement `SQLAlchemyUnitOfWork` — a concrete `UnitOfWork` that owns the SQLAlchemy `Session` lifecycle (create → share → commit/rollback → close). On `__enter__`, creates `Session` via injected `session_factory` and constructs 5 repos sharing that `Session`. On `commit()`, calls `session.commit()` then collects domain events from registered aggregate roots. On `__exit__`, auto-rollbacks on error; always `close()`.

## Architecture Decisions

### Decision: Event collection mechanism — `register_modified(root)` (idempotent)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **A: register_modified(root)** with `set[AggregateRoot]` | Explicit, caller must register. No FROZEN layer changes. **Idempotent by design.** | ✅ **Chosen** |
| B: Repo auto-tracking | Requires modifying repos (FROZEN — out of scope) | ❌ |
| C: session.new/dirty/deleted | No mapping from ORM model → domain aggregate root; fragile | ❌ |

**Rationale**: `register_modified()` is explicit, zero changes to FROZEN repos/services, perfectly testable. Uses `set[AggregateRoot]` internally — if a root is registered 5 times (e.g., `save` called repeatedly on the same entity), it appears exactly once during event collection. Sprint 5.4B will wire auto-tracking if needed.

### Decision: EventPublisher injection (preparation for 5.4B)

The UoW constructor accepts an optional `EventPublisher`. In 5.4A it's stored but NOT used. In 5.4B, the single line `if self._event_publisher: self._event_publisher.publish_many(events)` activates publication — no API change required.

```python
class EventPublisher(Protocol):
    """Stub Protocol — real implementation in Sprint 5.4B."""
    def publish_many(self, events: list[DomainEvent]) -> None: ...
```

### Decision: Session ownership — exclusive, managed by UoW

The `Session` is created inside `__enter__`, never exposed publicly, always closed in `__exit__`. Repos receive it via constructor (existing pattern). External code NEVER holds a reference to the `Session`.

**Rationale**: Prevents use-after-close bugs, ensures cleanup in all paths.

### Decision: Commit failure handling — rollback + PersistenceError

On `session.commit()` failure: rollback session internally, then raise `PersistenceError`. The `__exit__` will see the exception (if unhandled) and call `rollback()` again (idempotent on already-rolled-back session).

**Rationale**: SQLAlchemy requires rollback after commit failure; wrapping in `PersistenceError` gives callers a stable exception to catch.

## Class Design — Skeleton Code

```python
"""
SQLAlchemyUnitOfWork — Transaction lifecycle for Ingestion BC persistence.

Owns Session creation, 5-repo sharing, commit/rollback/close, and
post-commit domain event collection.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, Self

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from foundation.base.aggregate_root import AggregateRoot
from foundation.events.domain_event import DomainEvent

from ingestion.infrastructure.persistence.exceptions import PersistenceError
from ingestion.infrastructure.persistence.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyFeedRepository,
    SQLAlchemyNewsSourceRepository,
    SQLAlchemyRawArticleRepository,
    SQLAlchemyTopicRepository,
)


class EventPublisher(Protocol):
    """Stub Protocol — real implementation in Sprint 5.4B.

    Defines the contract for publishing collected domain events.
    The UoW stores this reference in 5.4A but does NOT call it yet.
    """

    def publish_many(self, events: list[DomainEvent]) -> None: ...


class SQLAlchemyUnitOfWork:
    """
    SQLAlchemy-backed Unit of Work.

    Owns Session lifecycle, shares it across 5 repos, manages
    commit/rollback/close, and collects domain events after
    successful commit.

    Attributes:
        news_sources: NewsSourceRepository (None before __enter__).
        feeds: FeedRepository (None before __enter__).
        raw_articles: RawArticleRepository (None before __enter__).
        categories: CategoryRepository (None before __enter__).
        topics: TopicRepository (None before __enter__).
        _collected_events: Domain events from the last successful commit().
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

    # ── Transaction control ───────────────────────────────────────────────

    def commit(self) -> None:
        """Persist changes, then collect domain events.

        Raises:
            PersistenceError: If session.commit() fails (session rolled back).
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

        Call after repo.save(root) to ensure the root's pending domain
        events are collected on the next commit().
        """
        self._modified_roots.add(root)

    def _collect_events(self) -> None:
        """Pull events from all modified roots. Clears tracking set."""
        for root in self._modified_roots:
            self._collected_events.extend(root.pull_events())
        self._modified_roots.clear()
```

## Data Flow

```
┌──────────────────────────────────────────────────────┐
│  Application Service                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │ with SQLAlchemyUoW() │  │ uow.register_modified│  │
│  │   repo.save(entity)  │──┤  (aggregate_root)    │  │
│  │   uow.commit()       │  └──────────┬───────────┘  │
│  └──────────┬───────────┘             │              │
└─────────────┼─────────────────────────┼──────────────┘
              │                         │
              ▼                         ▼
┌──────────────────────────────────────────────┐
│  SQLAlchemyUnitOfWork                         │
│                                              │
│  __enter__ → Session() + 5 repos ✂️ Session  │
│                                              │
│  commit():                                   │
│    1. session.commit()                       │
│    2. pull_events(modified_roots)            │
│    3. → _collected_events                    │
│                                              │
│  __exit__:                                   │
│    if exc_type → rollback()                  │
│    always → close()                          │
└──────────────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ingestion/infrastructure/persistence/unit_of_work.py` | Create | SQLAlchemyUnitOfWork class |
| `src/ingestion/infrastructure/persistence/__init__.py` | Modify | Export `SQLAlchemyUnitOfWork` in `__all__` |
| `tests/ingestion/infrastructure/conftest.py` | Modify | Add `uow_session` fixture |
| `tests/ingestion/infrastructure/test_unit_of_work.py` | Create | ~19 scenario tests |

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | Commit exactly once | Mock session_factory, assert `session.commit()` called 1× via spy |
| Unit | Commit failure | Mock `session.commit()` to raise `IntegrityError`, assert `PersistenceError` |
| Unit | Rollback on __exit__ error | Enter `with`, raise exception, assert `session.rollback()` called |
| Unit | Close always | Both success and error paths, assert `session.close()` called 1× |
| Unit | Idempotent close | `close()` twice — no error |
| Unit | Session identity | `repo1._session is repo2._session` |
| Unit | Flush visibility | Save via repo1, find via repo2 without explicit commit |
| Unit | Event collection | `register_modified(root_with_event)` + `commit()` → `_collected_events` contains event |
| Unit | No collection on rollback | `register_modified(root)` + rollback → `_collected_events` empty |
| Regression | All 1568 tests pass | `pytest tests/` — 0 failures |

### Fixture Design (conftest.py extension)

```python
@pytest.fixture
def uow(sqlite_session_factory):
    """Fresh SQLAlchemyUnitOfWork with SQLite in-memory."""
    from ingestion.infrastructure.persistence import SQLAlchemyUnitOfWork
    return SQLAlchemyUnitOfWork(sqlite_session_factory)
```

Tests use the existing `tables` fixture to create schema, then `uow` for the session lifecycle.

## Integration Points

- **Repos**: No changes needed — they already accept `Session` via constructor. UoW passes the same `Session` to all 5.
- **conftest.py**: New `uow` fixture uses `sqlite_session_factory` (existing). No existing fixtures broken.
- **`__init__.py`**: Add `SQLAlchemyUnitOfWork` to imports and `__all__`.
- **Existing tests**: Continue using `sqlite_session` fixture directly — no changes required.

## Error Handling

| Path | Action | Exception |
|------|--------|-----------|
| `session.commit()` fails | Rollback session, raise wrapped | `PersistenceError` |
| `__exit__` with exception | Call `rollback()` then `close()` | Original exception propagates |
| `commit()` called without session | Raise immediately | `PersistenceError("no active session")` |
| `close()` on already-closed | No-op | No exception |
| `rollback()` on already-rolled-back | No-op | No exception |

## Open Questions

- [ ] None resolved — all decisions documented above.
