# Exploration: EPIC 6 — Presentation Layer & External Adapters

**Date**: 2026-07-13
**Status**: COMPLETE — Ready for Proposal

---

## 1. Current State

### What Exists Today

The Ingestion BC is COMPLETE with 4 frozen layers:
- **Foundation v1.0** — Entity, AggregateRoot, Result[T], Error, DomainEvent, FoundationError hierarchy, ClockPort, UUIDProvider
- **Domain v2.0** — 3 AggregateRoots (NewsSource, Feed, RawArticle), 2 Entities (Category, Topic), 9 VOs, 3 Domain Events, 17 exception classes, 5 Repository Protocols
- **Application v1.0** — 3 Services (22 operations), 15 Commands, 6 Queries, 10 DTOs, 2 Ports (EventPublisher, UnitOfWork), ErrorMapper
- **Infrastructure v1.0** — 5 SQLAlchemy repos, SQLAlchemyUnitOfWork, SQLAlchemyEventPublisher, ORM models, Engine, Config

The existing `presentation/` directory contains OLD monolith code (pre-DDD):
- FastAPI routes for Research/Script/Topics (NOT Ingestion BC)
- Old Container (composition root) — no DDD wiring
- Old error handlers using `DomainError` from old domain module
- Old CLI commands

### What Needs to Be Built

A NEW Presentation Layer that:
1. Exposes the 22 Ingestion BC operations via REST API
2. Uses DDD-compliant composition root
3. Handles async-to-sync bridging (FastAPI is async, services are sync)
4. Maps Result[T] → HTTP responses
5. Maps ApplicationErrorCode → HTTP status codes
6. Validates requests via Pydantic models
7. Provides OpenAPI documentation

---

## 2. Dependencies Available

From `requirements.txt`:
- **FastAPI** >= 0.110.0
- **uvicorn[standard]** >= 0.29.0
- **Pydantic** >= 2.5.0
- **pytest** >= 8.0.0
- **pytest-asyncio** >= 0.23.0

No `pyproject.toml` — flat `requirements.txt` only.

---

## 3. Application Services (API Surface)

| # | Service | Method | Input | Output |
|---|---------|--------|-------|--------|
| 1 | SourceService | execute_register_source | RegisterSourceCommand | Result[SourceDetailDTO] |
| 2 | SourceService | execute_update_source | UpdateSourceCommand | Result[SourceDetailDTO] |
| 3 | SourceService | execute_enable_source | EnableSourceCommand | Result[SourceDetailDTO] |
| 4 | SourceService | execute_disable_source | DisableSourceCommand | Result[SourceDetailDTO] |
| 5 | SourceService | execute_assign_category_to_source | AssignCategoryToSourceCommand | Result[SourceDetailDTO] |
| 6 | SourceService | execute_assign_topic_to_source | AssignTopicToSourceCommand | Result[SourceDetailDTO] |
| 7 | SourceService | execute_find_source | FindSourceQuery | Result[SourceDetailDTO] |
| 8 | SourceService | execute_list_active_sources | ListActiveSourcesQuery | Result[QueryResult[SourceSummaryDTO]] |
| 9 | FeedService | execute_register_feed | RegisterFeedCommand | Result[FeedDetailDTO] |
| 10 | FeedService | execute_update_feed | UpdateFeedCommand | Result[FeedDetailDTO] |
| 11 | FeedService | execute_pause_feed | PauseFeedCommand | Result[FeedDetailDTO] |
| 12 | FeedService | execute_activate_feed | ActivateFeedCommand | Result[FeedDetailDTO] |
| 13 | FeedService | execute_record_collection | RecordCollectionCommand | Result[FeedDetailDTO] |
| 14 | FeedService | execute_record_failure | RecordFailureCommand | Result[FeedDetailDTO] |
| 15 | FeedService | execute_assign_category_to_feed | AssignCategoryToFeedCommand | Result[FeedDetailDTO] |
| 16 | FeedService | execute_assign_topic_to_feed | AssignTopicToFeedCommand | Result[FeedDetailDTO] |
| 17 | FeedService | execute_find_feed | FindFeedQuery | Result[FeedDetailDTO] |
| 18 | FeedService | execute_list_feeds | ListFeedsQuery | Result[QueryResult[FeedSummaryDTO]] |
| 19 | ArticleService | execute_create_article | CreateRawArticleCommand | Result[RawArticleDetailDTO] |
| 20 | ArticleService | execute_find_article | FindArticleQuery | Result[RawArticleDetailDTO] |
| 21 | ArticleService | execute_list_articles | ListArticlesQuery | Result[QueryResult[RawArticleSummaryDTO]] |

**Critical Pattern**: ALL services are SYNCHRONOUS. They return `Result[T]`, never raise exceptions.

---

## 4. Commands (frozen dataclasses — Request Shapes)

### Source Commands
| Command | Required Fields | Optional Fields |
|---------|----------------|-----------------|
| RegisterSourceCommand | name: str, source_type: str, source_url: str | — |
| UpdateSourceCommand | source_id: str | name?, source_type?, source_url? |
| EnableSourceCommand | source_id: str | — |
| DisableSourceCommand | source_id: str, reason: str | — |
| AssignCategoryToSourceCommand | source_id: str, category_id: str | — |
| AssignTopicToSourceCommand | source_id: str, topic_id: str | — |

### Feed Commands
| Command | Required Fields | Optional Fields |
|---------|----------------|-----------------|
| RegisterFeedCommand | source_id: str, url: str, label: str, language: str | sync_mode?, sync_interval_minutes?, sync_max_retries?, categories?, topics? |
| UpdateFeedCommand | feed_id: str | url?, label?, language?, sync_mode?, sync_interval_minutes?, sync_max_retries? |
| PauseFeedCommand | feed_id: str, reason: str | — |
| ActivateFeedCommand | feed_id: str | — |
| RecordCollectionCommand | feed_id: str, count: int | batch_id? |
| RecordFailureCommand | feed_id: str, error: str | — |
| AssignCategoryToFeedCommand | feed_id: str, category_id: str | — |
| AssignTopicToFeedCommand | feed_id: str, topic_id: str | — |

### Article Commands
| Command | Required Fields | Optional Fields |
|---------|----------------|-----------------|
| CreateRawArticleCommand | feed_id: str, external_id: str, content_hash: str, title: str, url: str | author?, language?, published_at?, fetched_at?, content_preview?, metadata? |

### Queries
| Query | Required Fields | Optional Fields |
|-------|----------------|-----------------|
| FindSourceQuery | source_id: str | — |
| ListActiveSourcesQuery | — | — |
| FindFeedQuery | feed_id: str | — |
| ListFeedsQuery | source_id: str | page?, size? |
| FindArticleQuery | article_id: str | — |
| ListArticlesQuery | feed_id: str | page?, size? |

---

## 5. DTOs (Response Shapes)

### Source DTOs
- **SourceSummaryDTO**: id, name, source_type, source_url, is_active
- **SourceDetailDTO**: id, name, source_type, source_url, is_active, categories(tuple), topics(tuple)

### Feed DTOs
- **FeedSummaryDTO**: id, source_id, url, label, language, is_active, retry_count
- **FeedDetailDTO**: id, source_id, url, label, language, is_active, sync_mode, sync_interval_minutes, sync_max_retries, categories(tuple), topics(tuple), retry_count

### Article DTOs
- **RawArticleSummaryDTO**: id, feed_id, title, url, author?, language?, published_at?, fetched_at?
- **RawArticleDetailDTO**: id, feed_id, external_id, content_hash, title, url, author?, language?, published_at?, fetched_at?, content_preview?, metadata?

### Category/Topic DTOs (no services yet)
- **CategorySummaryDTO**: id, name, slug, is_active
- **CategoryDetailDTO**: id, name, slug, parent_id?, is_active
- **TopicSummaryDTO**: id, name, is_active
- **TopicDetailDTO**: id, name, description?, is_active

### Common
- **QueryResult[T]**: data[], total?, page?, size?

---

## 6. Error Hierarchy & HTTP Mapping

### Foundation Errors
```
FoundationError (Exception)
├── DomainError          → 422 Unprocessable Entity
├── ApplicationError     → 400/404/500
└── InfrastructureError  → 503 Service Unavailable
```

### Ingestion Domain Errors (17 exception classes)
| Exception | code | HTTP Status | Category |
|-----------|------|-------------|----------|
| InvalidStateError | INVALID_STATE | 422 | General |
| InvalidSourceUrlError | INVALID_SOURCE_URL | 422 | Source |
| SourceAlreadyEnabledError | SOURCE_ALREADY_ENABLED | 409 | Source |
| SourceAlreadyDisabledError | SOURCE_ALREADY_DISABLED | 409 | Source |
| FeedAlreadyEnabledError | FEED_ALREADY_ENABLED | 409 | Feed |
| FeedAlreadyDisabledError | FEED_ALREADY_DISABLED | 409 | Feed |
| FeedAlreadyPausedError | FEED_ALREADY_PAUSED | 409 | Feed |
| FeedMaxRetriesExceededError | FEED_MAX_RETRIES_EXCEEDED | 409 | Feed |
| InvalidArticleUrlError | INVALID_ARTICLE_URL | 422 | Article |
| InvalidArticleTitleError | INVALID_ARTICLE_TITLE | 422 | Article |
| InvalidCategoryError | INVALID_CATEGORY | 422 | Category |
| DuplicateCategoryNameError | DUPLICATE_CATEGORY_NAME | 409 | Category |
| CycleDetectedError | CYCLE_DETECTED | 409 | Category |
| InvalidTopicError | INVALID_TOPIC | 422 | Topic |
| InvalidSyncPolicyError | INVALID_SYNC_POLICY | 422 | Feed |
| InvalidLanguageError | INVALID_LANGUAGE | 422 | Validation |

### IngestionErrorCode (domain enum — 16 codes)
Maps to ApplicationErrorCode via ErrorMapper:
| Domain Code | → Application Code | → HTTP Status |
|-------------|-------------------|---------------|
| NEWS_SOURCE_NOT_FOUND | RESOURCE_NOT_FOUND | 404 |
| FEED_NOT_FOUND | RESOURCE_NOT_FOUND | 404 |
| RAW_ARTICLE_NOT_FOUND | RESOURCE_NOT_FOUND | 404 |
| CATEGORY_NOT_FOUND | RESOURCE_NOT_FOUND | 404 |
| TOPIC_NOT_FOUND | RESOURCE_NOT_FOUND | 404 |
| DUPLICATE_NEWS_SOURCE | COMMAND_INVALID | 409 |
| DUPLICATE_FEED_URL | COMMAND_INVALID | 409 |
| DUPLICATE_ARTICLE | COMMAND_INVALID | 409 |
| INVALID_SOURCE_URL | COMMAND_INVALID | 422 |
| INVALID_ARTICLE_URL | COMMAND_INVALID | 422 |
| INVALID_LANGUAGE | COMMAND_INVALID | 422 |
| NEWS_SOURCE_INACTIVE | COMMAND_INVALID | 409 |
| FEED_INACTIVE | COMMAND_INVALID | 409 |
| HAS_ACTIVE_FEEDS | COMMAND_INVALID | 409 |
| CYCLE_DETECTED | COMMAND_INVALID | 409 |
| FEED_MAX_RETRIES_EXCEEDED | OPERATION_FAILED | 500 |
| FEED_ALREADY_PAUSED | COMMAND_INVALID | 409 |

### ApplicationErrorCode (6 codes)
| Code | HTTP Status |
|------|-------------|
| COMMAND_INVALID | 400 |
| COMMAND_MISSING_FIELD | 422 |
| RESOURCE_NOT_FOUND | 404 |
| OPERATION_FAILED | 500 |
| TRANSACTION_FAILED | 500 |
| CONCURRENCY_CONFLICT | 409 |

---

## 7. Ports (Application Layer)

| Port | Methods | Implementation |
|------|---------|----------------|
| **UnitOfWork** (Protocol) | __enter__, __exit__, commit(), rollback() | SQLAlchemyUnitOfWork |
| **EventPublisher** (Protocol) | publish(event), publish_many(events) | SQLAlchemyEventPublisher (in-memory) |

### Domain Repository Ports (5)
| Port | Key Methods | Implementation |
|------|-------------|----------------|
| NewsSourceRepository | save, find_by_id, find_by_name, find_all, find_active, exists_by_name | SQLAlchemyNewsSourceRepository |
| FeedRepository | save, find_by_id, find_by_source, find_by_url, find_active_by_source, exists_by_source_and_url, count_active_by_source | SQLAlchemyFeedRepository |
| RawArticleRepository | save, save_batch, find_by_id, find_by_feed, find_by_hash, exists_by_url, exists_by_hash, count_by_feed | SQLAlchemyRawArticleRepository |
| CategoryRepository | save, find_by_id, find_by_slug, find_all, find_active, find_by_parent, exists_by_slug | SQLAlchemyCategoryRepository |
| TopicRepository | save, find_by_id, find_by_name, find_all, find_active, exists_by_name | SQLAlchemyTopicRepository |

### Foundation Ports
| Port | Methods | Implementation |
|------|---------|----------------|
| ClockPort | now() → datetime | SystemClock (or test mock) |
| UUIDProvider | generate() → UUID | StandardUUIDProvider (or test mock) |

---

## 8. Existing Presentation Code (OLD Monolith)

### Old API Routes (6 files)
| Route | Prefix | Purpose | DDD Compatible? |
|-------|--------|---------|----------------|
| topics.py | /api/v1/topics | Research topics CRUD | NO — old research module |
| discover.py | /api/v1 | Auto-discover topics + status | NO — old research module |
| scheduler.py | /api/v1/scheduler | Scheduler control | NO — old research module |
| scripts.py | /api/v1/topics/{id}/script | Script generation | NO — old application module |
| studio.py | ? | Studio operations | NO — old module |
| script_list.py | ? | List scripts | NO — old module |

### Old Container
- `Container` class in `presentation/cli/container.py` — wires OLD modules
- `ApiContainer` extends Container — adds script module
- NO DDD wiring (no UnitOfWork, no EventPublisher, no repository protocols)

### Old Error Handlers
- `error_handlers.py` — catches DomainError from OLD domain module
- Uses old `ErrorMapper` from `application.error_mapper` (NOT the DDD one)

**CONCLUSION**: The existing `presentation/` is 100% OLD monolith code. EPIC 6 needs to create NEW presentation code alongside it (or replace it). The old code serves the Research/Script BC, not Ingestion.

---

## 9. Testing Patterns

### Test Organization
```
tests/
├── ingestion/
│   ├── application/
│   │   ├── conftest.py           # In-memory repos, UoW, services
│   │   ├── test_source_service.py
│   │   ├── test_feed_service.py
│   │   ├── test_article_service.py
│   │   ├── test_commands.py
│   │   ├── test_queries.py
│   │   ├── test_dtos.py
│   │   ├── test_error_mapper.py
│   │   ├── test_mappers.py
│   │   └── ...
│   ├── domain/
│   │   └── ... (entity, VO, event tests)
│   └── infrastructure/
│       └── ... (SQLAlchemy repo, UoW tests)
├── presentation/               # OLD monolith tests
│   ├── conftest.py             # PostgreSQL test DB
│   ├── test_api_routes.py
│   └── ...
└── ...
```

### Key Patterns
- `pytest.ini`: `asyncio_mode = auto`, `-m "not integration"`
- Test DB: PostgreSQL `test_system_shorts`
- In-memory repositories used in application tests (no DB dependency)
- `conftest.py` at application level creates in-memory repos and wires services

### Fixtures (from tests/ingestion/application/conftest.py)
- InMemoryNewsSourceRepository, InMemoryFeedRepository, etc.
- InMemoryUnitOfWork
- InMemoryEventPublisher
- SourceService, FeedService, ArticleService (wired with in-memory deps)

---

## 10. Key Technical Decisions for EPIC 6

### Decision 1: Async-to-Sync Bridging
**Problem**: FastAPI is async, but all Application Services are synchronous.
**Options**:
- A) `run_in_executor()` — run sync service in thread pool
- B) Make services async — requires changing all 22 methods + UoW
- C) Use `def` endpoints (not `async def`) — FastAPI runs in thread pool automatically
**Recommendation**: Option A or C. Don't change the frozen Application layer.

### Decision 2: Result[T] → HTTP Response
**Problem**: Services return `Result[T]`, not exceptions. FastAPI needs status codes.
**Options**:
- A) Extract `.is_success` in each endpoint, return appropriate response
- B) Create a `ResultToHTTPResponse` utility
- C) Create a FastAPI dependency that wraps Result → response
**Recommendation**: Option A in a thin adapter layer. Simple, explicit, no magic.

### Decision 3: Pydantic Models vs Frozen Dataclasses
**Problem**: Commands/DTOs are frozen dataclasses. FastAPI needs Pydantic for validation.
**Options**:
- A) Pydantic request models that convert to Commands (separate models)
- B) Use frozen dataclasses directly (FastAPI supports via `model_validate`)
- C) Auto-generate Pydantic from dataclass metadata
**Recommendation**: Option A. Pydantic models for HTTP validation, thin converter to Commands. Keeps frozen dataclasses clean.

### Decision 4: Composition Root Location
**Problem**: Where to wire services, repos, UoW for the NEW presentation?
**Options**:
- A) New `src/ingestion/presentation/container.py` inside the BC
- B) Replace old `presentation/api/container.py`
- C) Create `src/presentation/` as a new top-level module
**Recommendation**: Option A or C. Keep it inside or parallel to the BC, don't touch old code yet.

### Decision 5: Coexistence with Old Presentation
**Problem**: Old `presentation/` serves Research/Script. New one serves Ingestion.
**Options**:
- A) Run both side-by-side (different prefixes)
- B) Replace old entirely
- C) Keep old for now, plan migration in future EPIC
**Recommendation**: Option C. Don't touch old code. New Ingestion presentation goes in `src/ingestion/presentation/`.

---

## 11. Gaps for EPIC 6

### What's Missing (Must Design)

1. **Pydantic Request/Response Models** — HTTP-specific validation layer (15 request + 10 response models)
2. **HTTPErrorMapper** — Maps ApplicationErrorCode → HTTP status codes (extends existing ErrorMapper)
3. **Result → HTTP Response Adapter** — Converts Result[T] to proper HTTP responses
4. **Async-to-Sync Bridge** — Wraps sync services for async FastAPI endpoints
5. **Composition Root** — Wires SQLAlchemy repos, UoW, EventPublisher, Services for presentation
6. **FastAPI Router Modules** — 3 routers: sources, feeds, articles (22 endpoints total)
7. **Error Handlers** — FastAPI exception handlers for domain/app errors
8. **Pydantic → Command Converters** — Thin mapping from HTTP models to application commands
9. **Test Fixtures** — conftest.py with TestClient, mock services, in-memory repos
10. **OpenAPI Customization** — Tags, descriptions, examples for the 3 resource groups

### What Exists (Reuse)

1. **ErrorMapper** — Already maps domain→app codes. Extend for HTTP status.
2. **Mappers** — SourceMapper, FeedMapper, RawArticleMapper already convert entities→DTOs
3. **QueryResult[T]** — Pagination wrapper ready to use
4. **ApplicationErrorCode** — 6 codes that map cleanly to HTTP statuses
5. **Commands/Queries** — 21 frozen dataclasses with all fields defined
6. **DTOs** — 10 frozen dataclasses defining response shapes

### What NOT to Touch

1. **Foundation v1.0** — FROZEN
2. **Domain v2.0** — FROZEN
3. **Application v1.0** — FROZEN
4. **Infrastructure v1.0** — FROZEN
5. **Old presentation/** — Leave as-is (Research/Script BC)

---

## 12. Proposed API Endpoints

### Sources (`/api/v1/ingestion/sources`)
| Method | Path | Command | Description |
|--------|------|---------|-------------|
| POST | / | RegisterSourceCommand | Create new source |
| GET | / | ListActiveSourcesQuery | List active sources |
| GET | /{source_id} | FindSourceQuery | Get source by ID |
| PATCH | /{source_id} | UpdateSourceCommand | Update source |
| POST | /{source_id}/enable | EnableSourceCommand | Enable source |
| POST | /{source_id}/disable | DisableSourceCommand | Disable source |
| POST | /{source_id}/categories | AssignCategoryToSourceCommand | Assign category |
| POST | /{source_id}/topics | AssignTopicToSourceCommand | Assign topic |

### Feeds (`/api/v1/ingestion/sources/{source_id}/feeds`)
| Method | Path | Command | Description |
|--------|------|---------|-------------|
| POST | / | RegisterFeedCommand | Create feed under source |
| GET | / | ListFeedsQuery | List feeds for source |
| GET | /{feed_id} | FindFeedQuery | Get feed by ID |
| PATCH | /{feed_id} | UpdateFeedCommand | Update feed |
| POST | /{feed_id}/pause | PauseFeedCommand | Pause feed |
| POST | /{feed_id}/activate | ActivateFeedCommand | Activate feed |
| POST | /{feed_id}/collection | RecordCollectionCommand | Record successful fetch |
| POST | /{feed_id}/failure | RecordFailureCommand | Record failed fetch |
| POST | /{feed_id}/categories | AssignCategoryToFeedCommand | Assign category |
| POST | /{feed_id}/topics | AssignTopicToFeedCommand | Assign topic |

### Articles (`/api/v1/ingestion/feeds/{feed_id}/articles`)
| Method | Path | Command | Description |
|--------|------|---------|-------------|
| POST | / | CreateRawArticleCommand | Create article |
| GET | / | ListArticlesQuery | List articles for feed |
| GET | /{article_id} | FindArticleQuery | Get article by ID |

**Total: 21 endpoints** (matching 21 service operations)

---

## 13. Affected Areas

### New Files (EPIC 6)
- `src/ingestion/presentation/` — New directory (NOT touching old `presentation/`)
- `src/ingestion/presentation/api/` — FastAPI routers, error handlers
- `src/ingestion/presentation/models/` — Pydantic request/response models
- `src/ingestion/presentation/container.py` — DDD composition root
- `src/ingestion/presentation/errors.py` — HTTP error mapping
- `src/ingestion/presentation/converters.py` — Pydantic → Command converters
- `tests/ingestion/presentation/` — Test suite

### Existing Files (Read-Only Reference)
- `src/ingestion/application/services/*.py` — What we call
- `src/ingestion/application/commands/*.py` — What we convert to
- `src/ingestion/application/queries/*.py` — What we convert to
- `src/ingestion/application/dto/*.py` — What we receive
- `src/ingestion/application/errors/error_mapper.py` — Extend for HTTP
- `src/ingestion/application/ports/*.py` — UoW, EventPublisher
- `src/ingestion/infrastructure/persistence/unit_of_work.py` — Concrete UoW
- `src/ingestion/infrastructure/event_publisher.py` — Concrete publisher
- `app/config.py` — Settings (reuse for API config)

---

## 14. Risks

1. **Sync-in-Async**: Running sync services in async context needs careful thread pool management
2. **UoW Lifecycle**: SQLAlchemyUnitOfWork is a context manager — must not outlive the request
3. **Old Code Coexistence**: Must not break old `presentation/` routes while adding new ones
4. **Test Isolation**: New presentation tests must not depend on PostgreSQL (use in-memory)
5. **Error Double-Mapping**: Domain→Application→HTTP needs clean separation, not 3 nested mappers

---

## 15. Ready for Proposal

**YES** — The exploration is complete. All 22 operations are cataloged, all error codes mapped, all gaps identified.

The orchestrator should tell the user:
- We have 3 services with 22 operations to expose
- Old `presentation/` is NOT DDD — new code goes in `src/ingestion/presentation/`
- 5 key technical decisions need to be made (async bridging, Result→HTTP, Pydantic models, composition root, coexistence)
- All frozen layers remain untouched
