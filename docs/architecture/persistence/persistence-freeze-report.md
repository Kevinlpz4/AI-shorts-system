# Persistence Layer v1.0 — Freeze Report

**Date**: 2026-07-13
**Sprint**: 5.4.5 — Persistence Freeze & Architecture Review
**Scope**: Ingestion BC Persistence Layer
**Status**: FROZEN

---

## Executive Summary

This report presents the findings of a comprehensive, read-only audit of the Ingestion BC Persistence Layer across 8 dimensions: Repository contracts, ORM models, Transaction semantics, Event publication, Concurrency, Performance, Architecture compliance, and Documentation. The audit covered 17 infrastructure source files, 3 contract/port files, 8 test files, and 5 documentation artifacts — approximately 3,500 lines of infrastructure code.

The persistence layer demonstrates strong architectural discipline. All 34 Repository Protocol methods are implemented with correct signatures and return types across both SQLAlchemy and InMemory implementations. The Dependency Rule is fully respected — zero forbidden imports were found across all persistence files. Error translation is consistent: every repository translates `IntegrityError→DuplicateEntityError`, `StaleDataError→ConcurrentModificationError` (where applicable), and `SQLAlchemyError→PersistenceError`, all with proper exception chaining (`from exc`). The UnitOfWork correctly implements post-commit event publication per ADR-025, with publish failure preserving the commit.

The audit identified **0 Critical findings**, **3 Warning findings**, and **4 Suggestion-level findings**. The warnings relate to unnecessary JOINs in two ORM relationships (FeedModel.source and CategoryModel.parent, both `lazy="joined"` but not accessed in `_to_domain()`). No correctness bugs, no architectural violations, and no blocking issues were found. The prior freeze reports (repository-freeze-report.md and orm-freeze-report.md) accurately document the known limitations that were addressed in subsequent sprints.

**Verdict**: The persistence layer meets all requirements for a FROZEN status.

---

## Compliance Matrix

| ID | Requirement | Status | Severity | Evidence | Notes |
|----|-------------|--------|----------|----------|-------|
| R1 | Repository Protocol compliance | ✅ PASS | — | All 5 repos: 34/34 methods | All signatures match Protocol definitions |
| R2 | No forbidden imports | ✅ PASS | — | grep: 0 matches in all persistence files | No application.services, api, or presentation imports |
| R3 | Error translation chain | ✅ PASS | — | All repos: IntegrityError→DuplicateEntityError, StaleDataError→ConcurrentModificationError, SQLAlchemyError→PersistenceError | All use `from exc` chaining |
| R4 | `_loaded` strong reference cache | ✅ PASS | — | All 5 repos: `_loaded: dict[str, Model]` | Prevents WeakInstanceDict GC |
| R5 | No dead imports (InvalidStateError) | ✅ PASS | — | grep: 0 matches | Cleaned up in Sprint 5.3.6 |
| R6 | UoW Protocol compliance | ✅ PASS | — | unit_of_work.py:73-163 | __enter__, __exit__, commit, rollback all correct |
| R7 | ADR-025 event publication | ✅ PASS | — | unit_of_work.py:98-133 | Post-commit only, publish failure preserves commit |
| O1 | Model column types correct | ✅ PASS | — | models.py: all Mapped[] verified | All types match design spec |
| O2 | ForeignKeys have ondelete | ✅ PASS | — | models.py: 4 FKs with ondelete | CASCADE (3), RESTRICT (1), SET NULL (1) |
| O3 | Optimistic locking (version_id_col) | ✅ PASS | — | models.py: 4 mutable roots | RawArticle correctly excluded |
| O4 | Relationships viewonly=True | ✅ PASS | — | models.py: all relationships | No ORM-managed mutations |
| O5 | Cascades limited | ✅ PASS | — | models.py:183 | Only save-update, merge on NewsSourceModel.feeds |
| O6 | TypeDecorators cache_ok=True | ✅ PASS | — | types.py:78, decorators.py (all 7) | All TypeDecorators marked cache_ok |
| O7 | TypeDecorator roundtrip correct | ✅ PASS | — | types.py, decorators.py | process_bind_param ↔ process_result_value verified |
| T1 | UoW commit semantics | ✅ PASS | — | unit_of_work.py:98-133 | commit→collect→publish order correct |
| T2 | UoW rollback idempotent | ✅ PASS | — | unit_of_work.py:135-138 | Guard: `if self._session is not None` |
| T3 | UoW close idempotent | ✅ PASS | — | unit_of_work.py:140-144 | Sets _session = None after close |
| T4 | UoW __exit__ never swallows | ✅ PASS | — | unit_of_work.py:83-94 | Explicit `return None` |
| T5 | register_modified idempotent | ✅ PASS | — | unit_of_work.py:148-157 | Uses set, same root N times → once |
| T6 | UoW initializes 5 repos | ✅ PASS | — | unit_of_work.py:73-81 | All 5 repos created with shared session |
| T7 | UoW session not None guard | ✅ PASS | — | unit_of_work.py:109-110 | Raises PersistenceError if no session |
| E1 | Both publishers implement Protocol | ✅ PASS | — | event_publisher.py, inmemory/event_publisher.py | publish() + publish_many() present |
| E2 | Publish after commit (ADR-025 Case A) | ✅ PASS | — | unit_of_work.py:120 | _collect_events() + publish_many() after commit |
| E3 | Commit failure → no publish (ADR-025 Case B) | ✅ PASS | — | test_event_publisher.py:118-132 | Verified by test |
| E4 | Publish failure → commit preserved (ADR-025 Case C) | ✅ PASS | — | unit_of_work.py:125-130, test_event_publisher.py:134-155 | PersistenceError raised, no rollback |
| E5 | Events cleared after attempt | ✅ PASS | — | unit_of_work.py:131-133 | finally block clears _collected_events |
| E6 | Event ordering preserved | ✅ PASS | — | Both publishers use list.extend() | FIFO order maintained |
| C1 | StaleDataError in mutable repos | ✅ PASS | — | news_source.py:141, feed.py:147, category.py:102, topic.py:92 | All 4 mutable repos handle it |
| C2 | RawArticle NO StaleDataError (correct) | ✅ PASS | — | raw_article.py: immutable entity | Dead code at lines 101-106 (SUGGESTION) |
| C3 | version column in 4 mutable models | ✅ PASS | — | models.py: lines 165, 291, 456, 519 | All have Integer, default=1 |
| C4 | __mapper_args__ version_id_col | ✅ PASS | — | models.py: lines 202, 327, 478, 532 | All 4 mutable roots |
| C5 | _loaded prevents WeakInstanceDict GC | ✅ PASS | — | All repos: documented in comments | Strong reference pattern documented |
| P1 | No N+1 query patterns | ✅ PASS | — | All repos: no query inside loops | Checked all for-loop constructs |
| P2 | exists_by_* uses select(id).limit(1) | ✅ PASS | — | All exists methods verified | Minimal projection, not full select |
| P3 | count_by_* uses func.count() | ✅ PASS | — | feed.py:258, raw_article.py:241 | Correct aggregate usage |
| P4 | No unnecessary flush() calls | ✅ PASS | — | flush() only in save/save_batch paths | Appropriate for ORM |
| P5 | All lazy strategies explicit | ✅ PASS | — | models.py: all relationships have lazy= | select, selectin, or joined |
| P6 | No accidental lazy loading | ✅ PASS | — | All relationships have explicit lazy strategy | No implicit "lazy" default |
| A1 | Domain layer frozen (zero infra imports) | ✅ PASS | — | domain/ports/repositories.py: only domain + foundation | Verified |
| A2 | Application layer frozen (zero infra imports) | ✅ PASS | — | application/ports/*: only foundation + domain | Verified |
| A3 | Foundation layer frozen | ✅ PASS | — | ADR-021: FROZEN since Sprint 1.x | Verified |
| A4 | Persistence isolation (no forbidden deps) | ✅ PASS | — | grep across all persistence files: 0 matches | Clean dependency direction |
| A5 | Infrastructure only imports inner layers | ✅ PASS | — | All repos: only domain.* + foundation.* + application.ports.* | Correct |
| D1 | repository-freeze-report.md exists | ✅ PASS | — | docs/architecture/persistence/ | Current, accurate |
| D2 | orm-freeze-report.md exists | ✅ PASS | — | docs/architecture/persistence/ | Current, accurate |
| D3 | ADR-024 matches implementation | ✅ PASS | — | adr-024-typedecorator-strategy.md | EntityIdType generic, VOs, Enums, composite |
| D4 | ADR-025 matches implementation | ✅ PASS | — | adr-025-event-publication-strategy.md | Post-commit hooks, no rollback on publish fail |
| D5 | persistence-design.md aligns | ✅ PASS | — | persistence-design.md | Schema, constraints, indexes all match |

---

## 1. Repository Audit

### SQLAlchemyNewsSourceRepository
- **Protocol**: 6/6 methods — `save`, `find_by_id`, `find_by_name`, `find_all`, `find_active`, `exists_by_name` ✅
- **Imports**: Clean — no forbidden imports ✅
- **Error translation**: IntegrityError→DuplicateEntityError (`news_source.py:137-140`), StaleDataError→ConcurrentModificationError (`news_source.py:141-144`), SQLAlchemyError→PersistenceError (`news_source.py:145-148`) — all with `from exc` ✅
- **`_loaded` cache**: Present at `news_source.py:44` — populated in `save()` (line 128) and `find_by_id()` (line 163) ✅
- **`_sync_m2m`**: Correctly handles M:N sync for categories and topics via DELETE+INSERT pattern ✅
- **`exists_by_name`**: Uses `select(NewsSourceModel.id).where().limit(1)` — minimal projection ✅
- **Findings**: None

### SQLAlchemyFeedRepository
- **Protocol**: 7/7 methods — `save`, `find_by_id`, `find_by_source`, `find_by_url`, `find_active_by_source`, `exists_by_source_and_url`, `count_active_by_source` ✅
- **Imports**: Clean — no forbidden imports, no dead InvalidStateError import ✅
- **Error translation**: IntegrityError→DuplicateEntityError (`feed.py:143-146`), StaleDataError→ConcurrentModificationError (`feed.py:147-150`), SQLAlchemyError→PersistenceError (`feed.py:151-154`) — all with `from exc` ✅
- **`_loaded` cache**: Present at `feed.py:43` — populated in `save()` (line 131) and `find_by_id()` (line 168) ✅
- **Composite SyncPolicy**: Mapped via `composite()` in model, roundtrip verified in `_to_domain()` and `_to_model()` ✅
- **`count_active_by_source`**: Uses `func.count(FeedModel.id)` — correct aggregate ✅
- **Findings**: None

### SQLAlchemyRawArticleRepository
- **Protocol**: 8/8 methods — `save`, `save_batch`, `find_by_id`, `find_by_feed`, `find_by_hash`, `exists_by_url`, `exists_by_hash`, `count_by_feed` ✅
- **Imports**: Clean — no forbidden imports ✅
- **Error translation**: IntegrityError→DuplicateEntityError (`raw_article.py:95-100`), SQLAlchemyError→PersistenceError (`raw_article.py:107-110`) — all with `from exc` ✅
- **`_loaded` cache**: Present at `raw_article.py:38` — populated in `find_by_id()` (line 150) ✅
- **Immutability**: Correctly NO StaleDataError handling (except dead code at lines 101-106) ✅
- **`save_batch`**: Atomic via loop + single flush ✅
- **Findings**:
  - **S-01 (Suggestion)**: Dead `StaleDataError` except block at `raw_article.py:101-106`. RawArticle has no `version_id_col`, so StaleDataError can never be raised. Code is unreachable but harmless.

### SQLAlchemyCategoryRepository
- **Protocol**: 7/7 methods — `save`, `find_by_id`, `find_by_slug`, `find_all`, `find_active`, `find_by_parent`, `exists_by_slug` ✅
- **Imports**: Clean — no forbidden imports ✅
- **Error translation**: IntegrityError→DuplicateEntityError (`category.py:98-101`), StaleDataError→ConcurrentModificationError (`category.py:102-105`), SQLAlchemyError→PersistenceError (`category.py:106-109`) — all with `from exc` ✅
- **`_loaded` cache**: Present at `category.py:37` — populated in `save()` (line 90) and `find_by_id()` (line 123) ✅
- **Self-referencing hierarchy**: `parent_id` FK with `ondelete="SET NULL"` ✅
- **Findings**: None

### SQLAlchemyTopicRepository
- **Protocol**: 6/6 methods — `save`, `find_by_id`, `find_by_name`, `find_all`, `find_active`, `exists_by_name` ✅
- **Imports**: Clean — no forbidden imports ✅
- **Error translation**: IntegrityError→DuplicateEntityError (`topic.py:88-91`), StaleDataError→ConcurrentModificationError (`topic.py:92-95`), SQLAlchemyError→PersistenceError (`topic.py:96-99`) — all with `from exc` ✅
- **`_loaded` cache**: Present at `topic.py:36` — populated in `save()` (line 81) and `find_by_id()` (line 113) ✅
- **Findings**: None

### Cross-Repository Summary
- **Total Protocol methods**: 34/34 (100%) ✅
- **Cross-repo imports**: 0 (zero imports between repos) ✅
- **Forbidden imports**: 0 across all 5 repositories ✅
- **`_loaded` cache**: Present in all 5 repos, consistently documented ✅
- **Error translation pattern**: Identical pattern across all repos (IntegrityError→Duplicate, StaleDataError→Concurrent, SQLAlchemyError→Persistence) ✅
- **UoW wiring**: All 5 repos initialized in `SQLAlchemyUnitOfWork.__enter__()` with shared session ✅

---

## 2. ORM Audit

### Models

#### NewsSourceModel (`models.py:137-209`)
- **Table**: `ingestion_news_sources`
- **Columns**: 8 (id, name, source_type, source_url, is_active, version, created_at, updated_at) ✅
- **PK**: `SourceId` via `EntityIdType(SourceId)` ✅
- **version_id_col**: `version` column (Integer, default=1) + `__mapper_args__ = {"version_id_col": version}` ✅
- **Relationships**: `feeds` (1:N, lazy="select", viewonly), `categories` (M:N, lazy="selectin", viewonly), `topics` (M:N, lazy="selectin", viewonly) ✅
- **Constraints**: `uq_news_source_name`, index on `is_active` ✅

#### FeedModel (`models.py:212-334`)
- **Table**: `ingestion_feeds`
- **Columns**: 16 (id, source_id, url, label, language, is_active, sync_mode, interval_minutes, max_retries, backoff_multiplier, max_backoff_minutes, timeout_seconds, max_items_per_run, retry_count, version, created_at, updated_at) ✅
- **FK**: `source_id → ingestion_news_sources.id` with `ondelete="CASCADE"` ✅
- **Composite SyncPolicy**: `composite(SyncPolicy, ...)` mapping 7 columns → 1 VO ✅
- **version_id_col**: `version` column + `__mapper_args__` ✅
- **Relationships**: `source` (N:1, lazy="joined", viewonly), `categories` (M:N, lazy="selectin", viewonly), `topics` (M:N, lazy="selectin", viewonly) ✅
- **Constraints**: `uq_feed_source_url`, composite index on (source_id, is_active) ✅

#### RawArticleModel (`models.py:337-416`)
- **Table**: `ingestion_raw_articles`
- **Columns**: 12 (id, feed_id, external_id, content_hash, title, url, author, language, published_at, fetched_at, content_preview, provider_metadata) + created_at ✅
- **FK**: `feed_id → ingestion_feeds.id` with `ondelete="RESTRICT"` ✅
- **NO version column**: Correct for immutable entity ✅
- **NO `__mapper_args__`**: Correct — no version_id_col ✅
- **Constraints**: 2 UQ (feed_id+external_id, feed_id+content_hash), 1 CK (hash length = 64) ✅
- **JSON column**: `provider_metadata` mapped to `"metadata"` DB column with `JSON(none_as_null=False)` ✅
- **Indexes**: 2 (feed_id+fetched_at desc, feed_id+url) ✅

#### CategoryModel (`models.py:419-490`)
- **Table**: `ingestion_categories`
- **Columns**: 9 (id, name, slug, description, is_active, parent_id, version, created_at, updated_at) ✅
- **FK**: `parent_id → ingestion_categories.id` (self-referencing) with `ondelete="SET NULL"` ✅
- **version_id_col**: `version` column + `__mapper_args__` ✅
- **Relationships**: `parent` (N:1 self-ref, lazy="joined", viewonly) ✅
- **Constraints**: `uq_category_slug`, `ck_category_no_self_parent`, indexes on parent_id and is_active ✅

#### TopicModel (`models.py:493-539`)
- **Table**: `ingestion_topics`
- **Columns**: 7 (id, name, description, is_active, version, created_at, updated_at) ✅
- **version_id_col**: `version` column + `__mapper_args__` ✅
- **No relationships**: Simplest model ✅
- **Constraints**: `uq_topic_name`, index on is_active ✅

### TypeDecorators

| TypeDecorator | File | impl | cache_ok | Roundtrip |
|---------------|------|------|----------|-----------|
| `EntityIdType[T]` | types.py:44 | Uuid | ✅ | EntityId → UUID → EntityId ✅ |
| `ArticleTitleType` | decorators.py:53 | String(500) | ✅ | ArticleTitle.value → str → ArticleTitle(str) ✅ |
| `ArticleUrlType` | decorators.py:77 | String(2048) | ✅ | ArticleUrl.value → str → ArticleUrl(str) ✅ |
| `CategoryNameType` | decorators.py:101 | String(100) | ✅ | CategoryName.value → str → CategoryName(str) ✅ |
| `SourceUrlType` | decorators.py:125 | String(2048) | ✅ | SourceUrl.value → str → SourceUrl(str) ✅ |
| `LanguageType` | decorators.py:149 | String(2) | ✅ | Language.code → str → Language(str) ✅ |
| `SourceTypeType` | decorators.py:180 | String(20) | ✅ | SourceType.value → str → SourceType(str) ✅ |
| `SyncModeType` | decorators.py:205 | String(20) | ✅ | SyncMode.value → str → SyncMode(str) ✅ |

**Note**: `LanguageType` correctly uses `.code` instead of `.value` — documented in docstring.

### Optimistic Locking

| Model | version column | version_id_col | Correct? |
|-------|---------------|----------------|----------|
| NewsSourceModel | ✅ Integer, default=1 | ✅ `__mapper_args__` | ✅ |
| FeedModel | ✅ Integer, default=1 | ✅ `__mapper_args__` | ✅ |
| CategoryModel | ✅ Integer, default=1 | ✅ `__mapper_args__` | ✅ |
| TopicModel | ✅ Integer, default=1 | ✅ `__mapper_args__` | ✅ |
| RawArticleModel | ❌ Absent | ❌ Absent | ✅ Correct (immutable) |

### Cascades & Relationships

| Relationship | lazy | viewonly | cascade | Assessment |
|-------------|------|----------|---------|------------|
| NewsSourceModel.feeds | select | ✅ | save-update, merge | ✅ Correct |
| NewsSourceModel.categories | selectin | ✅ | — | ✅ Correct (M:N) |
| NewsSourceModel.topics | selectin | ✅ | — | ✅ Correct (M:N) |
| FeedModel.source | joined | ✅ | — | ⚠️ Unnecessary JOIN |
| FeedModel.categories | selectin | ✅ | — | ✅ Correct (M:N) |
| FeedModel.topics | selectin | ✅ | — | ✅ Correct (M:N) |
| CategoryModel.parent | joined | ✅ | — | ⚠️ Unnecessary JOIN |

---

## 3. Transaction Audit

### SQLAlchemyUnitOfWork

- **commit semantics**: ✅ Correct — calls `_session.commit()`, then `_collect_events()`, then `publish_many()` (in that exact order)
- **rollback semantics**: ✅ Correct — idempotent, guards with `if self._session is not None`
- **close semantics**: ✅ Correct — idempotent, sets `_session = None` after close
- **register_modified**: ✅ Correct — uses `set()` for idempotency, same root N times → exactly once during collection
- **Event collection**: ✅ Correct — `_collect_events()` iterates `_modified_roots`, calls `pull_events()`, clears tracking set
- **Context manager**: ✅ Correct — `__exit__` returns `None` (never swallows exceptions), auto-rollback on error, always close
- **__enter__**: ✅ Correct — creates session + initializes all 5 repos with shared session

### InMemoryUnitOfWork

- **Protocol compliance**: `__enter__`, `__exit__`, `commit`, `rollback` — all present ✅
- **LSP with SQLAlchemyUnitOfWork**: Partial — InMemoryUnitOfWork does NOT have repo attributes (`news_sources`, `feeds`, etc.) ✅ **NOT A REAL ISSUE** — Application services receive repos via DI constructor injection, NOT via `uow.news_sources`. The UoW is only used for `commit()`/`rollback()`.
- **Behavior**: Tracks committed/rolled_back state for test assertions ✅
- **Missing**: No `close()` method (not in Protocol, so not required) ✅

---

## 4. Event Publication Audit

### ADR-025 Compliance

| Case | Expected | Actual | Status |
|------|----------|--------|--------|
| **Case A: Happy path** | Publish after commit | `_collect_events()` after `session.commit()`, then `publish_many()` | ✅ |
| **Case B: Commit failure** | No publish | Commit exception caught → PersistenceError raised → publish never reached | ✅ |
| **Case C: Publish failure** | Commit preserved | `PersistenceError` raised with `from exc`, commit NOT rolled back (lines 125-130) | ✅ |

### Event Ordering
- **Preserved**: ✅ Both publishers use `list.extend()` which preserves insertion order

### Duplicate Prevention
- **Possible**: ✅ `_modified_roots` is a `set`, so same root registered N times → `pull_events()` called exactly once

### Event Cleanup
- **Cleared after attempt**: ✅ `finally` block at `unit_of_work.py:131-133` clears `_collected_events` regardless of publish success/failure

---

## 5. Concurrency Audit

### Optimistic Locking

| Aggregate | version_id_col | StaleDataError handled | ConcurrentModificationError raised | Tests verify |
|-----------|---------------|----------------------|-----------------------------------|--------------|
| NewsSource | ✅ | ✅ (`news_source.py:141`) | ✅ | ✅ (`test_concurrency.py`) |
| Feed | ✅ | ✅ (`feed.py:147`) | ✅ | ✅ (`test_concurrency.py`) |
| Category | ✅ | ✅ (`category.py:102`) | ✅ | ✅ (`test_concurrency.py`) |
| Topic | ✅ | ✅ (`topic.py:92`) | ✅ | ✅ (`test_concurrency.py`) |
| RawArticle | ❌ (immutable) | Dead code (`raw_article.py:101`) | N/A | ✅ (not tested, correct) |

### Strong Reference Cache

- **`_loaded` pattern**: ✅ Present in all 5 SQLAlchemy repos
- **Documentation**: ✅ All repos include comment: "Strong reference cache: prevents WeakInstanceDict invalidation from clearing the identity map entry when this method returns"
- **Consistent usage**: ✅ All repos populate `_loaded` after `session.get()` and after `_to_model()` in save paths

---

## 6. Performance Audit

### N+1 Patterns
- **Found**: 0. No query patterns inside loops. All `find_all()` / `find_active()` / `find_by_source()` / `find_by_feed()` methods load collections in a single query with lazy strategies.

### Unnecessary JOINs
- **Found**: 2 (low impact)
  1. `FeedModel.source` (`lazy="joined"`) — `_to_domain()` does NOT access `model.source`, only `model.source_id` (line `feed.py:54`). The JOIN is wasted.
  2. `CategoryModel.parent` (`lazy="joined"`) — `_to_domain()` does NOT access `model.parent`, only `model.parent_id` (line `category.py:51`). The JOIN is wasted.

### Batch Opportunities
- **`save_batch()`**: Uses loop ORM `session.add()` + single `flush()`. Functional but not optimized for large batches. Already documented in repository-freeze-report.md (Sprint 5.3.5).

### Identity Map Usage
- **Correct**: `session.get()` leverages SQLAlchemy identity map. `_loaded` prevents GC from removing entries from WeakInstanceDict.

### Unnecessary Flushes
- **Found**: 0. `flush()` is called only in `save()` and `save_batch()` paths — appropriate for ORM workflow.

### Accidental Lazy Loading
- **Found**: 0. All relationships have explicit `lazy` strategy set. No SQLAlchemy default "lazy" loading in use.

---

## 7. Architecture Audit

### Dependency Rule

| Layer | Status | Evidence |
|-------|--------|----------|
| Foundation FROZEN | ✅ Verified | ADR-021: frozen since Sprint 1.x |
| Domain FROZEN | ✅ Verified | domain/ports/repositories.py: only imports domain entities + foundation Result |
| Application FROZEN | ✅ Verified | application/ports/*: only imports foundation + domain |
| Persistence isolation | ✅ Compliant | Zero forbidden imports across all persistence files |

### Layer Dependencies

```
Foundation (FROZEN)
  ↑
Domain (FROZEN) ← defines Protocol ports
  ↑
Application (FROZEN) ← defines Port interfaces (EventPublisher, UnitOfWork)
  ↑
Infrastructure/Persistence ← implements Protocols (repos, UoW, event publishers)
```

All arrows point inward. No reverse dependencies. Clean Architecture fully respected.

### Forbidden Import Scan Results

| Pattern | Files scanned | Matches |
|---------|---------------|---------|
| `from ingestion.application.services` | 17 persistence files | 0 |
| `from ingestion.api` | 17 persistence files | 0 |
| `from ingestion.presentation` | 17 persistence files | 0 |
| `from ingestion.infrastructure.persistence.repositories` in domain | 1 domain file | 0 |

---

## 8. Documentation Audit

| Document | Exists | Current | Complete |
|----------|--------|---------|----------|
| persistence-freeze-report.md | ✅ (this document) | ✅ 2026-07-13 | ✅ |
| repository-freeze-report.md | ✅ | ✅ 2026-07-05 | ✅ All findings accurately documented |
| orm-freeze-report.md | ✅ | ✅ 2026-07-05 | ✅ All findings accurately documented |
| persistence-design.md | ✅ | ✅ Current | ✅ Aligns with code |
| orm-mapping-strategy.md | ✅ | ✅ Current | ✅ Relationships match code |
| adr-024-typedecorator-strategy.md | ✅ | ✅ Current | ✅ Matches actual implementation |
| adr-025-event-publication-strategy.md | ✅ | ✅ Current | ✅ Matches actual implementation |
| transaction-strategy.md | ✅ | ✅ Current | ✅ UoW strategy matches code |

---

## Findings Summary

### Critical (must fix before freeze)
**None**

### Warning (should fix)

| ID | Finding | File(s) | Evidence | Recommendation |
|----|---------|---------|----------|----------------|
| W-01 | Unnecessary JOIN: FeedModel.source | `models.py:306-310` | `lazy="joined"` but `_to_domain()` at `feed.py:54` only accesses `model.source_id`, not `model.source` | Change to `lazy="select"` |
| W-02 | Unnecessary JOIN: CategoryModel.parent | `models.py:471-475` | `lazy="joined"` but `_to_domain()` at `category.py:51` only accesses `model.parent_id`, not `model.parent` | Change to `lazy="select"` |
| W-03 | SQLAlchemyEventPublisher naming misleading | `event_publisher.py:14` | Class name suggests SQLAlchemy usage, but it's an in-memory publisher (no SQLAlchemy dependency). The docstring says "In-memory Domain Event publisher." | Rename to `InProcessEventPublisher` or document naming rationale |

### Suggestion (nice to have)

| ID | Finding | File(s) | Evidence | Recommendation |
|----|---------|---------|----------|----------------|
| S-01 | Dead StaleDataError except block in RawArticle | `raw_article.py:101-106` | RawArticle is immutable (no version_id_col in model), so StaleDataError can never be raised by SQLAlchemy | Remove unreachable except block |
| S-02 | CategoryModel.parent `viewonly=True` not enforced | `models.py:471-475` | parent relationship has `viewonly=True` but the flag is set via `relationship()` — SQLAlchemy allows writes to viewonly relationships (they silently do nothing) | No action needed; viewonly is correctly set |
| S-03 | InMemoryUnitOfWork lacks repo attributes | `inmemory/unit_of_work.py` | No `news_sources`, `feeds` etc. attributes like SQLAlchemyUnitOfWork | Not a real issue — repos are injected via DI, not accessed via UoW |
| S-04 | Two event publishers with similar core behavior | `event_publisher.py`, `inmemory/event_publisher.py` | Both implement EventPublisher Protocol identically. InMemoryEventPublisher has extras (clear, has_event, published_events). SQLAlchemyEventPublisher is actually in-memory too. | Document the distinction (test utility vs production placeholder) |

---

## Known Issues Investigation

### Issue #1: Duplicate Event Publishers
**Status**: NOT a real issue — distinct roles

Both `SQLAlchemyEventPublisher` (infrastructure/event_publisher.py) and `InMemoryEventPublisher` (infrastructure/inmemory/event_publisher.py) implement the `EventPublisher` Protocol with identical core methods (`publish`, `publish_many`). However, they serve different contexts:

- `SQLAlchemyEventPublisher` is the **default publisher** injected into `SQLAlchemyUnitOfWork` when no external publisher is configured. Despite its name, it's purely in-memory (stores events in `self.events`). The naming is misleading — it does NOT use SQLAlchemy.
- `InMemoryEventPublisher` is the **test utility** publisher with extra inspection methods (`clear()`, `has_event()`, `published_events`).

**Verdict**: Not duplicates. `SQLAlchemyEventPublisher` should be renamed (S-04) to avoid confusion, but this is cosmetic.

### Issue #2: RawArticle StaleDataError Dead Code
**Status**: CONFIRMED dead code — SUGGESTION severity

At `raw_article.py:101-106`, there's an `except StaleDataError` block that maps to `DuplicateEntityError`. However:
- RawArticleModel has NO `version` column and NO `__mapper_args__` with `version_id_col`
- Without `version_id_col`, SQLAlchemy cannot raise `StaleDataError`
- The except block is unreachable

**Verdict**: Dead code. Not harmful, but should be removed for clarity.

### Issue #3: Dead InvalidStateError Import
**Status**: ALREADY RESOLVED

Grep confirms zero `InvalidStateError` imports across all 5 repository files. The dead imports documented in repository-freeze-report.md (W-01) were cleaned up in Sprint 5.3.6.

**Verdict**: No action needed.

### Issue #4: InMemoryUnitOfWork LSP Gap
**Status**: NOT A REAL ISSUE

The investigation reveals that Application Services receive repositories via **constructor DI** (`self._source_repo`, `self._feed_repo`, etc.), NOT via `uow.news_sources`. The UoW is used exclusively for `commit()` and `rollback()`. Evidence:

- `source_service.py:83-84`: `self._source_repo = source_repo; self._feed_repo = feed_repo`
- `source_service.py:120-121`: `self._source_repo.save(source); self._uow.commit()`
- No `uow.news_sources` usage found in any application service

**Verdict**: The UoW Protocol only requires `__enter__`, `__exit__`, `commit`, `rollback`. Repo attributes on `SQLAlchemyUnitOfWork` are a convenience for test wiring (seen in `test_concurrency.py`), not part of the contract. `InMemoryUnitOfWork` is LSP-compliant for the Protocol as defined.

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Unnecessary JOINs (FeedModel.source, CategoryModel.parent) | LOW — small catalog tables, minimal performance impact | Change to `lazy="select"` in next sprint |
| Misleading event publisher naming | LOW — code readability only | Document or rename in future sprint |
| Dead StaleDataError in RawArticle | NONE — unreachable code, no runtime impact | Remove for code clarity |

---

## Recommendations

1. **[Optional, low priority]** Change `FeedModel.source` from `lazy="joined"` to `lazy="select"` and `CategoryModel.parent` from `lazy="joined"` to `lazy="select"` to eliminate unnecessary JOINs.
2. **[Optional, low priority]** Rename `SQLAlchemyEventPublisher` to something more accurate (e.g., `InProcessEventPublisher`) to reflect that it's an in-memory publisher, not a SQLAlchemy-dependent one.
3. **[Optional, low priority]** Remove the dead `StaleDataError` except block in `raw_article.py:101-106`.

None of these recommendations block the freeze. They are cosmetic improvements for future sprints.

---

## Freeze Declaration

> # PERSISTENCE LAYER v1.0 — FROZEN
>
> By this document, the Architecture Review Board officially declares
> the **Ingestion BC Persistence Layer v1.0** as **FROZEN** effective
> July 13, 2026.
>
> ## Scope of Freeze
>
> | Component | Status |
> |-----------|--------|
> | SQLAlchemyNewsSourceRepository | FROZEN |
> | SQLAlchemyFeedRepository | FROZEN |
> | SQLAlchemyRawArticleRepository | FROZEN |
> | SQLAlchemyCategoryRepository | FROZEN |
> | SQLAlchemyTopicRepository | FROZEN |
> | SQLAlchemyUnitOfWork | FROZEN |
> | persistence/base.py | FROZEN |
> | persistence/types.py | FROZEN |
> | persistence/decorators.py | FROZEN |
> | persistence/models.py | FROZEN |
> | persistence/exceptions.py | FROZEN |
> | persistence/engine.py | FROZEN |
> | persistence/config.py | FROZEN |
> | SQLAlchemyEventPublisher | FROZEN |
> | InMemory repositories | FROZEN |
> | InMemoryUnitOfWork | FROZEN |
> | InMemoryEventPublisher | FROZEN |
> | All test files | FROZEN |
>
> ## Implications
>
> 1. No new methods may be added to repositories without RFC.
> 2. No Protocol signatures may change without RFC.
> 3. Bug fixes are allowed without RFC (pass test suite).
> 4. Recommended improvements documented above may be addressed in future sprints.
>
> ## Prior Layers (FROZEN)
>
> | Layer | Sprint |
> |-------|--------|
> | Foundation | 1.x |
> | Domain | 2.x–3.x |
> | Application | 4.x |
> | Persistence Foundation | 5.1 |
> | ORM Layer | 5.2.5 |
> | Repository Layer | 5.3.5 |
> | **Persistence Layer (complete)** | **5.4.5** |

**Frozen by**: ARB
**Date**: 2026-07-13
**Scope**: Ingestion BC Persistence Layer v1.0
**Next review**: When unfrozen via RFC

---

## ARB Verdict

- [ ] **APPROVED** — All requirements met, no critical findings
- [x] **APPROVED WITH SUGGESTIONS** — Minor findings, non-blocking
- [ ] **REJECTED** — Critical findings must be resolved

**Verdict**: **APPROVED WITH SUGGESTIONS**

**Rationale**: The persistence layer fully meets all 48 compliance requirements (R1-R7, O1-O7, T1-T7, E1-E6, C1-C5, P1-P6, A1-A5, D1-D5). Zero critical findings. Three warnings and four suggestions are all low-impact cosmetic improvements that do not affect correctness, security, or architectural integrity. The prior freeze reports (repository-freeze-report.md, orm-freeze-report.md) accurately documented known limitations from earlier sprints, and all have been addressed or are accepted as known technical debt.

**Conditions**: None — all suggestions are non-blocking.
