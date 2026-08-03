# Persistence — SQLAlchemyUnitOfWork

## Purpose

Transactional integrity for Ingestion BC persistence. UoW owns Session lifecycle: creation, sharing across 5 repos, commit/rollback/close with automatic error handling.

## Requirements

### R1: UoW Creation

`SQLAlchemyUnitOfWork` MUST accept `session_factory` and optional `event_publisher`. On `__enter__`, MUST create `Session` and init all 5 repos with it.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 1 | After init | `SQLAlchemyUnitOfWork(factory)` | inspect | repos are `None` |
| 2 | On enter | `SQLAlchemyUnitOfWork(factory)` | `uow.__enter__()` | `Session` created, 5 repos initialized |

### R2: Commit Lifecycle

`commit()` MUST call `session.commit()` exactly once, then collect events from aggregate roots.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 3 | Happy path | modified entities in UoW | `commit()` | `session.commit()` called 1× |
| 4 | Event collection | roots with pending events | `commit()` succeeds | events pulled from each root |
| 5 | Commit failure | SQLAlchemyError on commit | `commit()` | `PersistenceError` raised |

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

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 15 | Post-commit | root with pending events | `commit()` succeeds | events in `_collected_events` |
| 16 | No commit | root with pending events | `__exit__` without `commit()` | events NOT collected |
| 17 | After rollback | root with pending events | rollback + `__exit__` | events NOT collected |
| 18 | Multiple roots | two roots, each with events | `commit()` succeeds | events from BOTH collected |
| 19 | Idempotent register | same root registered 5 times | `commit()` succeeds | root appears exactly once |

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
