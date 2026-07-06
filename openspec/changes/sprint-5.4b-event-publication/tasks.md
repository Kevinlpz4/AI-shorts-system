# Tasks: Sprint 5.4B — Domain Event Publication

## Phase 1: Infrastructure Implementation

- [x] T1: Create `SQLAlchemyEventPublisher` in `src/ingestion/infrastructure/event_publisher.py`
  - Implements `EventPublisher` Protocol from `application.ports`
  - `publish()` — stores single event in `self.events`
  - `publish_many()` — extends `self.events` preserving order

- [x] T2: Update `unit_of_work.py` — remove stub Protocol, update imports
  - Delete local `EventPublisher(Protocol)` class
  - Add `from ingestion.application.ports.event_publisher import EventPublisher`
  - Remove `Protocol` from `typing` import (keep `Self`)
  - Update docstring referencing stub location

- [x] T3: Update `unit_of_work.py` — integrate `publish_many()` in `commit()`
  - After `_collect_events()`, call `self._event_publisher.publish_many(self._collected_events)`
  - Skip if `event_publisher is None` or `_collected_events` empty
  - On publish failure: raise `PersistenceError`, NO rollback
  - Clear `_collected_events` after publish (in finally / always-clear pattern)

## Phase 2: Tests

- [x] T4: Unit tests for `SQLAlchemyEventPublisher`
  - `test_publish_stores_single_event`
  - `test_publish_many_stores_multiple_events`
  - `test_publish_many_preserves_order`
  - `test_publish_many_with_empty_list`
  - `test_publisher_is_observable`

- [x] T5: Integration tests (UoW + EventPublisher)
  - `test_commit_publishes_collected_events`
  - `test_commit_without_publisher_skips_publication`
  - `test_commit_failure_does_not_publish`
  - `test_publish_failure_does_not_rollback`
  - `test_commit_twice_without_changes`

## Phase 3: Validation

- [x] T6: Non-regression — run `python -m pytest tests/ -x --tb=short`
