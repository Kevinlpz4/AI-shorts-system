# Persistence — Unit of Work & Event Publication

## Purpose

Transactional integrity for Ingestion BC persistence. The `SQLAlchemyUnitOfWork` owns the Session lifecycle: creation, sharing across the 5 repositories, commit/rollback/close with automatic error handling. After a successful commit, domain events are collected from aggregate roots and published through the `EventPublisher` Protocol (extracted to its own module, with the concrete `SQLAlchemyEventPublisher` implementation) per ADR-025.

## Requirements

### R1: UoW Creation

`SQLAlchemyUnitOfWork` MUST accept `session_factory` and optional `event_publisher`. On `__enter__`, MUST create `Session` and init all 5 repos with it.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 1 | After init | `SQLAlchemyUnitOfWork(factory)` | inspect | repos are `None` |
| 2 | On enter | `SQLAlchemyUnitOfWork(factory)` | `uow.__enter__()` | `Session` created, 5 repos initialized |

### R2: Commit Lifecycle

`commit()` MUST call `session.commit()` exactly once, then collect events from aggregate roots. After `session.commit()` and `_collect_events()`, `commit()` MUST call `self._event_publisher.publish_many(self._collected_events)` if publisher is not None.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 3 | Happy path | modified entities in UoW | `commit()` | `session.commit()` called 1× |
| 4 | Event collection | roots with pending events | `commit()` succeeds | events pulled from each root |
| 5 | Commit failure | SQLAlchemyError on commit | `commit()` | `PersistenceError` raised |
| 28 | Publish after collect | modified root + publisher in UoW | `commit()` | `publish_many` called with collected events |
| 29 | Skip if no publisher | modified root, `publisher=None` | `commit()` | publish NOT called (backward compat) |

### R3: Rollback Lifecycle

`rollback()` MUST call `session.rollback()`. `__exit__` MUST auto-rollback if `exc_type` is not None.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 6 | Explicit | uncommitted changes in UoW | `rollback()` | `session.rollback()` called |
| 7 | Auto on error | exception inside `with` block | `__exit__` with `exc_type` | rollback called before close |

### R4: Close Lifecycle

`__exit__` MUST always call `session.close()` (success or failure). `close()` SHALL be idempotent.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 8 | Normal exit | UoW exits without exception | `__exit__` | `session.close()` called |
| 9 | Error exit | UoW exits with exception | `__exit__` | `session.close()` after rollback |
| 10 | Idempotent | session already closed | call `close()` again | no error |

### R5: Context Manager

UoW MUST support `with` statement. Each instance SHALL manage its own `Session` independently.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 11 | Basic usage | `with UoW(factory) as uow:` | inside block | `uow.session` exists, repos accessible |
| 12 | Nested | two independent UoW instances | nest them | each has own `Session` |

### R6: Cross-Repo Session Consistency

All repos in same UoW MUST share the exact same `Session`.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 13 | Same Session | UoW active with 2 repos | `repo1._session is repo2._session` | `True` (same identity) |

### R7: Event Collection

Events MUST be collected from aggregate roots ONLY after successful `commit()`. No collection if commit skipped or rollback occurred.

Registering the same root multiple times MUST be idempotent (the root appears exactly once during collection).

After successful publication, `_collected_events` MUST be cleared. No clearing if publish fails (UoW delegates failure to caller).

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 15 | Post-commit | root with pending events | `commit()` succeeds | events in `_collected_events` |
| 16 | No commit | root with pending events | `__exit__` without `commit()` | events NOT collected |
| 17 | After rollback | root with pending events | rollback + `__exit__` | events NOT collected |
| 18 | Multiple roots | two roots, each with events | `commit()` succeeds | events from BOTH collected |
| 19 | Idempotent register | same root registered 5 times | `commit()` succeeds | root appears exactly once |
| 30 | Clear after publish | events collected and published | `commit()` returns | `_collected_events` is empty |

### R8: No Regression

MUST NOT break the existing 1568 tests.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 20 | Full suite | 1568 existing tests | run full suite | 0 failures |

### R9: Session Identity Chain

ALL 5 repos MUST share the exact same `Session` object identity. This is the fundamental purpose of the Unit of Work — a single transaction across all repositories.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 14 | Identity chain | UoW active with all 5 repos | `s is news_sources._session is feeds._session is ...` | `True` across all 5 |

### R10: EventPublisher Protocol (Extracted)

The `EventPublisher` Protocol MUST move from `unit_of_work.py` to `event_publisher.py`. It MUST define both `publish()` and `publish_many()`. `unit_of_work.py` MUST import from the new location.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 21 | Protocol in new module | `event_publisher.py` exists | import `EventPublisher` | has `publish()` and `publish_many()` |
| 22 | UoW imports from new location | `unit_of_work.py` | inspect import | from `ingestion.infrastructure.event_publisher` |

### R11: SQLAlchemyEventPublisher

A concrete `SQLAlchemyEventPublisher` MUST implement the `EventPublisher` Protocol. Events MUST be stored in `self.events: list[DomainEvent]`. `publish_many()` MUST preserve insertion order. MUST NOT perform external IO.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 23 | Single publish | fresh publisher | `publish(e)` | `events == [e]` |
| 24 | Bulk with order | fresh publisher | `publish_many([e1, e2])` | `events == [e1, e2]` |

### R12: Publish Failure Policy

When `publish_many()` raises inside `commit()`, the system MUST propagate `PersistenceError`. The session MUST NOT be rolled back (commit already succeeded). Per ADR-025 Opción A, this is a known limitation: some events may be published before the failure.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 25 | Publish fails after commit | commit succeeded, publisher raises | `commit()` returns | `PersistenceError`, `session` NOT rolled back |

### R13: Event Ordering

Events MUST be published in the same order they were collected from aggregate roots.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 26 | Insertion order | root→e1 registered, then root→e2 | `commit()` | `publish_many([e1, e2])` preserves sequence |

### R14: Idempotent Second Commit

Calling `commit()` twice without new modifications MUST NOT publish duplicates.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 27 | Second commit no-op | one commit already done | `commit()` again | `publish_many([])` — no-op |

### R15: Backward Compatibility

MUST NOT break existing tests.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 31 | 19 UoW tests pass | Sprint 5.4A test suite | run `test_unit_of_work.py` | 0 failures |
| 32 | Full suite passes | all 1587 existing tests | run full suite | 0 failures |
