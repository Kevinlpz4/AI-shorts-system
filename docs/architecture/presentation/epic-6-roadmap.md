# EPIC 6 — Implementation Roadmap (Updated)

**Last updated**: Sprint 6.3B (Presentation Completion)
**Design version**: v1.0 FROZEN

---

## Sprint 6.0: Design Freeze ✅

- Resolve 4 ARB warnings (W-01 through W-04)
- Create ADR-026, ADR-027, ADR-028
- Formalize freeze declaration
- **Status**: COMPLETE

## Sprint 6.1: Presentation Foundation ✅

**Dependencies**: 6.0
**Actual tests**: 61 (exceeded estimate of 20-30)
**Status**: COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| 6.1.1 | FastAPI app factory (`app.py` with lifespan) | ✅ |
| 6.1.2 | Settings class (pydantic-settings, `AI_SHORTS_` prefix, `extra="ignore"`) | ✅ |
| 6.1.3 | Lifespan hooks (engine creation/disposal on app.state) | ✅ |
| 6.1.4 | Dependency providers (`dependencies.py`: settings, UoW, services) | ✅ |
| 6.1.5 | Middleware stack: RequestID → CorrelationID → Timing → Recovery | ✅ |
| 6.1.6 | Exception handlers (RFC 9457 Problem Details, 5 handlers) | ✅ |
| 6.1.7 | OpenAPI configuration (tags, metadata, docs URLs) | ✅ |
| 6.1.8 | Health endpoints (`/health/live`, `/health/ready` with DI) | ✅ |
| 6.1.9 | Structured logging (stdlib JSON formatter, RequestContextFilter) | ✅ |
| 6.1.10 | Sync→async bridge (TEMPORAL, `bridge/sync_async.py`) | ✅ |
| 6.1.11 | Unit + integration tests (61 tests, 8 test files) | ✅ |

## Sprint 6.2: Core API — Source + Feed ✅

**Dependencies**: 6.1
**Actual tests**: 56 (21 Source + 35 Feed; exceeded estimate of 40-55)
**Status**: COMPLETE

Source + Feed endpoints together (Feed depends on Source).

### Sprint 6.2A: Source API ✅

10 endpoints implemented, 21 tests, all passing.

| Endpoint | Operation | HTTP | Status |
|----------|-----------|------|--------|
| `POST /api/v1/sources` | RegisterSource | 201 | ✅ |
| `GET /api/v1/sources` | ListSources (paginated) | 200 | ✅ |
| `GET /api/v1/sources/{id}` | GetSource | 200 | ✅ |
| `PUT /api/v1/sources/{id}` | UpdateSource | 200 | ✅ |
| `POST /api/v1/sources/{id}/activate` | ActivateSource | 200 | ✅ |
| `POST /api/v1/sources/{id}/deactivate` | DeactivateSource | 200 | ✅ |
| `POST /api/v1/sources/{id}/categories` | AssignCategoryToSource | 204 | ✅ |
| `DELETE /api/v1/sources/{id}/categories/{category_id}` | RemoveCategoryFromSource | 204 | ✅ |
| `POST /api/v1/sources/{id}/topics` | AssignTopicToSource | 204 | ✅ |
| `DELETE /api/v1/sources/{id}/topics/{topic_id}` | RemoveTopicFromSource | 204 | ✅ |

### Sprint 6.2B: Feed API ✅

12 endpoints implemented, 35 tests, all passing.

| Endpoint | Operation | HTTP | Status |
|----------|-----------|------|--------|
| `POST /api/v1/sources/{id}/feeds` | RegisterFeed | 201 | ✅ |
| `PUT /api/v1/sources/{id}/feeds/{feed_id}` | UpdateFeed | 200 | ✅ |
| `GET /api/v1/sources/{id}/feeds/{feed_id}` | GetFeed | 200 | ✅ |
| `GET /api/v1/sources/{id}/feeds` | ListFeeds (paginated) | 200 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/activate` | ActivateFeed | 200 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/deactivate` | DeactivateFeed | 200 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/pause` | PauseFeed | 200 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/sync` | RecordCollection | 204 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/failure` | RecordFailure | 204 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/categories` | AssignCategoryToFeed | 204 | ✅ |
| `DELETE /api/v1/sources/{id}/feeds/{feed_id}/categories/{category_id}` | RemoveCategoryFromFeed | 204 | ✅ |
| `POST /api/v1/sources/{id}/feeds/{feed_id}/topics` | AssignTopicToFeed | 204 | ✅ |
| `DELETE /api/v1/sources/{id}/feeds/{feed_id}/topics/{topic_id}` | RemoveTopicFromFeed | 204 | ✅ |

## Sprint 6.3A: Application Completion — Category + Topic Services ✅

**Dependencies**: 6.2
**Actual tests**: 30 (15 Category + 15 Topic; exceeded estimate of 25-35)
**Status**: COMPLETE

Complete the Application Layer for Category and Topic CRUD. No modifications to existing files — only new additions.

| Task | Description | Status |
|------|-------------|--------|
| 6.3A.1 | Category Commands: CreateCategoryCommand, UpdateCategoryCommand, ActivateCategoryCommand, DeactivateCategoryCommand | ✅ |
| 6.3A.2 | Category Queries: FindCategoryQuery, ListCategoriesQuery | ✅ |
| 6.3A.3 | CategoryService: execute_create, execute_update, execute_find, execute_list, execute_activate, execute_deactivate | ✅ |
| 6.3A.4 | Category Mapper: Entity → DTO (summary + detail) | ✅ (pre-existing) |
| 6.3A.5 | Topic Commands: CreateTopicCommand, UpdateTopicCommand, ActivateTopicCommand, DeactivateTopicCommand | ✅ |
| 6.3A.6 | Topic Queries: FindTopicQuery, ListTopicsQuery | ✅ |
| 6.3A.7 | TopicService: execute_create, execute_update, execute_find, execute_list, execute_activate, execute_deactivate | ✅ |
| 6.3A.8 | Topic Mapper: Entity → DTO (summary + detail) | ✅ (pre-existing) |
| 6.3A.9 | DI providers: get_category_service, get_topic_service | ✅ |
| 6.3A.10 | Tests: CategoryService + TopicService (unit, 30 tests) | ✅ |

**Notes**:
- Category and Topic are Entities (not AggregateRoots) — no event system, no `pull_events()`
- Duplicate slug check uses `DuplicateCategoryNameError` (domain exception)
- Duplicate name check for Topic uses `ApplicationErrorCode.COMMAND_INVALID` (no domain exception exists)
- Mappers and DTOs were pre-existing from the design phase

## Sprint 6.3B: Presentation Completion — Category + Topic + Article API ✅

**Dependencies**: 6.3A
**Actual tests**: 43 (11 Article + 15 Category + 15 Topic + 2 OpenAPI; exceeded estimate of 40-50)
**Status**: COMPLETE

Complete the Presentation Layer for all remaining Content API endpoints.

| Endpoint | Operation | HTTP | Status |
|----------|-----------|------|--------|
| `POST /api/v1/articles` | CreateArticle | 201 | ✅ |
| `GET /api/v1/articles` | ListArticles (paginated, by feed_id) | 200 | ✅ |
| `GET /api/v1/articles/{id}` | GetArticle | 200 | ✅ |
| `POST /api/v1/categories` | CreateCategory | 201 | ✅ |
| `GET /api/v1/categories` | ListCategories | 200 | ✅ |
| `GET /api/v1/categories/{id}` | GetCategory | 200 | ✅ |
| `PUT /api/v1/categories/{id}` | UpdateCategory | 200 | ✅ |
| `POST /api/v1/categories/{id}/activate` | ActivateCategory | 200 | ✅ |
| `POST /api/v1/categories/{id}/deactivate` | DeactivateCategory | 200 | ✅ |
| `POST /api/v1/topics` | CreateTopic | 201 | ✅ |
| `GET /api/v1/topics` | ListTopics | 200 | ✅ |
| `GET /api/v1/topics/{id}` | GetTopic | 200 | ✅ |
| `PUT /api/v1/topics/{id}` | UpdateTopic | 200 | ✅ |
| `POST /api/v1/topics/{id}/activate` | ActivateTopic | 200 | ✅ |
| `POST /api/v1/topics/{id}/deactivate` | DeactivateTopic | 200 | ✅ |

**Notes**:
- Article list requires `feed_id` query param (ListArticlesQuery dependency)
- Category/Topic activate/deactivate return 200 (entity with updated `is_active` state)
- DELETE for categories/topics uses UoW directly (services lack remove methods)
- All 43 tests pass, zero regressions against 1756+ existing tests

## Sprint 6.4: Observability & Operations ✅

**Dependencies**: 6.3B
**Actual tests**: ~25 (enhanced middleware, logging, health, OpenAPI + new performance baseline)
**Status**: COMPLETE

Verify and harden all observability, diagnostics, and operational capabilities defined in ADR-028.

| Task | Description | Status |
|------|-------------|--------|
| 6.4.1 | Request ID: auto-generate, preserve client, propagate to logs | ✅ |
| 6.4.2 | Correlation ID: propagate HTTP → middleware → dependencies → application → logs | ✅ |
| 6.4.3 | Timing middleware: precision, X-Request-Duration header, no response impact | ✅ |
| 6.4.4 | Structured logging: JSON, all required fields (timestamp, level, request_id, correlation_id, method, path, status, duration_ms, exception) | ✅ |
| 6.4.5 | Exception logging: Problem Details + structured log with stacktrace for 5xx only | ✅ |
| 6.4.6 | Health endpoints: liveness, readiness (DB up/down), SessionFactory invalid | ✅ |
| 6.4.7 | OpenAPI: tags, operationId, schemas, version, contact, license, servers, no orphan endpoints | ✅ |
| 6.4.8 | Performance baseline: CRUD Source/Feed/Article, p95 < 100ms SQLite InMemory | ✅ |
| 6.4.9 | Production checklist: all categories PASS | ✅ |
| 6.4.10 | Documentation: observability-audit.md, performance-baseline.md, production-readiness.md | ✅ |

## Sprint 6.5: Security & API Hardening ✅

**Dependencies**: 6.4
**Actual tests**: 39
**Status**: COMPLETE

API Hardening — Production Readiness 92.5% → 100%.

| Task | Description | Status |
|------|-------------|--------|
| 6.5.1 | CORS configuration hardening (no wildcard, validator) | ✅ |
| 6.5.2 | TrustedHost middleware (configurable, wildcard support) | ✅ |
| 6.5.3 | Rate limiting audit — deferred per YAGNI (ADR-029) | ✅ |
| 6.5.4 | Security headers (HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP, Permissions-Policy) | ✅ |
| 6.5.5 | Configuration validation (SECRET_KEY, CORS, LOG_FORMAT, ENVIRONMENT validators + startup check) | ✅ |
| 6.5.6 | OpenAPI review — all endpoints documented, tags, operationId | ✅ |
| 6.5.7 | Idempotency review — deferred (no idempotent operations needed yet) | ✅ |
| 6.5.8 | Error surface audit — no stack traces, consistent Problem Details | ✅ |

## Sprint 6.6: E2E, Audit & Presentation Freeze

**Dependencies**: 6.5
**Estimated tests**: TBD
**Status**: NOT STARTED

| Task | Description |
|------|-------------|
| 6.6.1 | E2E tests (full lifecycle) |
| 6.6.2 | Smoke tests |
| 6.6.3 | Final ARB audit of Presentation Layer |
| 6.6.4 | Deployment documentation |
| 6.6.5 | Presentation Layer v1.0 declared FROZEN |

---

## Summary

| Metric | Value |
|--------|-------|
| Total sprints | 9 (6.0 - 6.6) |
| Total endpoints | 37 (10 Source + 12 Feed + 3 Article + 6 Category + 6 Topic) + 2 health = 39 |
| Total actual tests | 229 (61 Foundation + 21 Source + 35 Feed + 30 App Completion + 43 Presentation Completion + 39 API Hardening) |
| Existing tests (frozen layers) | 1115+ |
| Grand total tests | 1838+ |

## Milestones

| Milestone | Sprint | Criteria | Status |
|-----------|--------|----------|--------|
| M1: App Boots | 6.1 | FastAPI starts, middleware works, DI resolves | ✅ COMPLETE |
| M2: Core API | 6.2 | Source + Feed endpoints functional | ✅ COMPLETE |
| M3A: App Completion | 6.3A | Category + Topic services, commands, queries, mappers | ✅ COMPLETE |
| M3B: Content API | 6.3B | Article + Category + Topic endpoints functional | ✅ COMPLETE |
| M4: Observability | 6.4 | Logging, metrics, performance verified | ✅ COMPLETE |
| M5: Security Hardening | 6.5 | CORS, TrustedHost, security headers, config validation | ✅ COMPLETE |
| M6: Presentation Freeze | 6.6 | E2E tests, ARB audit, final freeze | NOT STARTED |

---

*See also: `presentation-design.md`, `testing-strategy.md`, `freeze-review.md`*
