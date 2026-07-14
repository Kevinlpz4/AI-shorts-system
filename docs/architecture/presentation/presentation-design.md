# Design: Presentation Layer & External Adapters

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Status**: Design-only
**Date**: 2026-07-13

---

## 1. Architecture Overview

The Presentation Layer is the outermost adapter in the Hexagonal Architecture. It translates HTTP requests into Application Layer commands/queries and Application DTOs into HTTP responses. It depends ONLY on the Application Layer — never on Domain or Infrastructure.

```
                    ┌─────────────────────────────────────────────┐
                    │            PRESENTATION LAYER                │
                    │                                              │
  HTTP Request ──▶  │  FastAPI Router                              │
                    │    ├── Request → Pydantic Model              │
                    │    ├── Pydantic Model → Command/Query        │
                    │    ├── Sync→Async Bridge (temporal)          │
                    │    │                                         │
                    │  Application Service (sync)                 │
                    │    ├── Command/Query → Result[T]             │
                    │    ├── Result[T] → HTTP Response             │
                    │    │                                         │
                    │  Exception Handlers                          │
                    │    └── Error → RFC 9457 Problem Details      │
                    │                                              │
                    │  Middleware Stack                             │
                    │    ├── Request ID / Correlation ID           │
                    │    ├── Timing / Access Log                   │
                    │    └── Exception Log                         │
                    └─────────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────────┐
                    │         APPLICATION LAYER (FROZEN)           │
                    │  SourceService · FeedService · ArticleService │
                    │  Commands · Queries · DTOs · ErrorMapper     │
                    └─────────────────────────────────────────────┘
```

## 2. Layer Boundaries

| Concern | Presentation Layer | Application Layer | Domain Layer |
|---------|-------------------|-------------------|-------------|
| HTTP parsing | ✅ Pydantic models | ❌ | ❌ |
| Validation (request) | ✅ Pydantic + custom validators | ❌ | ❌ |
| Business rules | ❌ | ❌ | ✅ |
| Command/Query construction | ✅ from Pydantic → dataclass | ❌ | ❌ |
| Result → HTTP mapping | ✅ | ❌ | ❌ |
| Error → HTTP status | ✅ via ErrorToProblemDetails | ❌ | ❌ |
| DTO → JSON serialization | ✅ Pydantic Response models | ❌ | ❌ |
| Transaction management | ❌ | ✅ via UnitOfWork | ❌ |
| Event publication | ❌ | ✅ via EventPublisher | ❌ |

## 3. File Structure

```
src/ingestion/presentation/
├── __init__.py
├── main.py                          # FastAPI app factory + lifespan
├── dependencies.py                  # Request-scoped DI functions
├── providers.py                     # Factory functions for services
├── lifespan.py                      # Startup/shutdown hooks
│
├── middleware/
│   ├── __init__.py
│   ├── request_id.py               # X-Request-ID injection
│   ├── correlation_id.py           # X-Correlation-ID propagation
│   ├── timing.py                   # Request duration measurement
│   └── access_log.py              # Structured access logging
│
├── exceptions/
│   ├── __init__.py
│   ├── handlers.py                 # FastAPI exception handlers
│   ├── problem_details.py          # RFC 9457 Problem Details model
│   └── error_mapper.py             # Error → HTTP status + Problem Details
│
├── models/
│   ├── __init__.py
│   ├── requests/
│   │   ├── __init__.py
│   │   ├── source_requests.py      # CreateSourceRequest, UpdateSourceRequest, etc.
│   │   ├── feed_requests.py        # CreateFeedRequest, UpdateFeedRequest, etc.
│   │   ├── article_requests.py     # CreateArticleRequest
│   │   └── common.py               # PaginationParams, PathID
│   ├── responses/
│   │   ├── __init__.py
│   │   ├── source_responses.py     # SourceResponse, SourceListResponse
│   │   ├── feed_responses.py       # FeedResponse, FeedListResponse
│   │   ├── article_responses.py    # ArticleResponse, ArticleListResponse
│   │   ├── health_responses.py     # HealthResponse, ReadinessResponse
│   │   └── paginated.py            # PaginatedResponse[T]
│   └── openapi/
│       ├── __init__.py
│       └── tags.py                 # OpenAPI tag definitions
│
├── routers/
│   ├── __init__.py
│   ├── sources.py                  # /api/v1/sources/*
│   ├── feeds.py                    # /api/v1/feeds/*, /api/v1/sources/{id}/feeds
│   ├── articles.py                 # /api/v1/articles/*, /api/v1/feeds/{id}/articles
│   ├── categories.py               # /api/v1/categories/*  (stub — no service yet)
│   ├── topics.py                   # /api/v1/topics/*      (stub — no service yet)
│   └── system.py                   # /health, /api/v1/info
│
└── bridge/
    ├── __init__.py
    └── sync_async.py               # run_sync() — TEMPORAL bridge
```

## 4. Design Principles Applied

| Principle | Application |
|-----------|-------------|
| **Dependency Rule** | Presentation → Application → Domain. NEVER backwards. |
| **Adapter Pattern** | Presentation is an HTTP adapter for Application Services |
| **Single Responsibility** | Each router file handles one aggregate root |
| **Open/Closed** | New endpoints = new router, no modification of existing |
| **Ubiquitous Language** | API names match domain operations (ActivateFeed, not UpdateStatus) |
| **API-First** | OpenAPI spec is source of truth; Pydantic models define contract |
| **Fail-Safe** | All errors mapped to RFC 9457; no 500 leaks |

## 5. Decision Traceability

| Decision | Design Choice | Document Reference |
|----------|--------------|-------------------|
| D1: Async-First | Sync endpoints with localized bridge | `bridge/sync_async.py` |
| D2: Composition Root | Pythonic DI via FastAPI Depends | `dependency-injection.md`, `composition-root.md` |
| D3: RFC 9457 | Problem Details for all errors | `exception-handling.md` |
| D4: API-First | Pydantic models define contract | `api-design.md` |
| D5: Ubiquitous Language | Domain operation names in API | `api-design.md` |
| D6: Versioning | `/api/v1` prefix | `routing-strategy.md` |
| D7: Health Endpoints | Separated liveness/readiness | `observability.md` |
| D8: Observability | Middleware stack from day one | `observability.md` |
| D9: OpenAPI as Contract | Tags, summaries, examples | `api-design.md` |
| D10: Idempotency | POST retry safety via headers | `idempotency-strategy.md` |

## 6. Evolution Roadmap

```
Phase 1 (Today):
  FastAPI (sync def endpoints)
      │  ← sync→async bridge (thread pool) — TEMPORAL
      ▼
  Application Services (sync)
      │
      ▼
  SQLAlchemy Repos (sync)
      │
      ▼
  PostgreSQL / SQLite (sync)

Phase 2 (Future — when DB driver supports it):
  FastAPI (async def endpoints)
      │  ← native async — bridge REMOVED
      ▼
  Application Services (async)
      │
      ▼
  SQLAlchemy Async Repos
      │
      ▼
  PostgreSQL (asyncpg)
```

The bridge pattern (`run_sync()` in `bridge/sync_async.py`) is a TEMPORAL adapter. It wraps sync Application Service calls in `asyncio.get_event_loop().run_in_executor()`. When the entire stack goes async, this file is DELETED — no other layer is affected.

## 7. Key Constraints

1. **No modifications to frozen layers**: Foundation v1.0, Domain v2.0, Application v1.0, Persistence v1.0 remain untouched.
2. **Old presentation code**: The existing `src/presentation/` (Research/Script BC) is NOT modified or imported.
3. **Category/Topic services**: No Application Service exists yet. Routers return 501 stubs.
4. **Test compatibility**: All 823+ existing tests must continue passing.

---

*See also: `api-design.md`, `exception-handling.md`, `composition-root.md`, `dependency-injection.md`*
