# Delta for Persistence — Event Publication (Sprint 5.4B)

## ADDED Requirements

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

## MODIFIED Requirements

### R2: Commit Lifecycle (extended)

After `session.commit()` and `_collect_events()`, `commit()` MUST call `self._event_publisher.publish_many(self._collected_events)` if publisher is not None.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 28 | Publish after collect | modified root + publisher in UoW | `commit()` | `publish_many` called with collected events |
| 29 | Skip if no publisher | modified root, `publisher=None` | `commit()` | publish NOT called (backward compat) |

### R7: Event Collection (extended)

After successful publication, `_collected_events` MUST be cleared. No clearing if publish fails (UoW delegates failure to caller).

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 30 | Clear after publish | events collected and published | `commit()` returns | `_collected_events` is empty |

## Non-Regression

### R15: Backward Compatibility

MUST NOT break existing tests.

| # | Scenario | Given | When | Then |
|---|----------|-------|------|------|
| 31 | 19 UoW tests pass | Sprint 5.4A test suite | run `test_unit_of_work.py` | 0 failures |
| 32 | Full suite passes | all 1587 existing tests | run full suite | 0 failures |
