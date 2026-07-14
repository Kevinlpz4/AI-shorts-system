# Design: Routing Strategy

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D5 (Ubiquitous Language), D6 (Versioning)

---

## 1. Router Organization

One router per aggregate root. Sub-routers for nested resources. All composed in `main.py` under `/api/v1`.

```
main.py (app factory)
│
├── /api/v1
│   ├── sources.py          → SourcesRouter (prefix: /sources)
│   ├── feeds.py            → FeedsRouter (prefix: /feeds)
│   ├── articles.py         → ArticlesRouter (prefix: /articles)
│   ├── categories.py       → CategoriesRouter (prefix: /categories) — stub
│   ├── topics.py           → TopicsRouter (prefix: /topics) — stub
│   └── system.py           → SystemRouter (prefix: /info)
│
├── /health                 → SystemRouter (separate prefix, no /api/v1)
│   ├── /live
│   └── /ready
```

## 2. Router Files

### sources.py — `SourcesRouter`

```python
router = APIRouter(prefix="/sources", tags=["Sources"])

# CRUD
router.post("/", ...)                          # RegisterSource
router.put("/{source_id}", ...)                # UpdateSource
router.patch("/{source_id}", ...)              # UpdateSource (partial)
router.get("/{source_id}", ...)                # FindSource
router.get("/", ...)                           # ListActiveSources

# State operations
router.post("/{source_id}/activate", ...)      # EnableSource
router.post("/{source_id}/deactivate", ...)    # DisableSource

# Relationships
router.post("/{source_id}/categories", ...)    # AssignCategoryToSource
router.post("/{source_id}/topics", ...)        # AssignTopicToSource

# Nested: feeds under source
router.include_router(feeds_router, prefix("/{source_id}/feeds"))
```

### feeds.py — `FeedsRouter`

```python
router = APIRouter(tags=["Feeds"])  # No prefix — included in sources + standalone

# Standalone CRUD (flat URLs)
router.post("/feeds", ...)                      # RegisterFeed (standalone)
router.put("/feeds/{feed_id}", ...)             # UpdateFeed
router.patch("/feeds/{feed_id}", ...)           # UpdateFeed (partial)
router.get("/feeds/{feed_id}", ...)             # FindFeed

# State operations
router.post("/feeds/{feed_id}/activate", ...)   # ActivateFeed
router.post("/feeds/{feed_id}/deactivate", ...) # PauseFeed

# Sync operations
router.post("/feeds/{feed_id}/sync", ...)       # RecordCollection

# Relationships
router.post("/feeds/{feed_id}/categories", ...) # AssignCategoryToFeed
router.post("/feeds/{feed_id}/topics", ...)     # AssignTopicToFeed
```

**Dual mounting**: The feeds router is mounted both:
1. Flat: `/api/v1/feeds/{feed_id}` (standalone access)
2. Nested: `/api/v1/sources/{source_id}/feeds` (scoped to source for listing)

### articles.py — `ArticlesRouter`

```python
router = APIRouter(tags=["Articles"])

router.post("/feeds/{feed_id}/articles", ...)    # CreateArticle
router.get("/articles/{article_id}", ...)        # FindArticle (flat)
router.get("/feeds/{feed_id}/articles", ...)     # ListArticles
```

### categories.py — `CategoriesRouter` (Stub)

```python
router = APIRouter(prefix="/categories", tags=["Categories"])

# All endpoints return 501 Not Implemented
router.post("/", ...)              # 501
router.put("/{category_id}", ...)  # 501
router.delete("/{category_id}", ...) # 501
router.get("/{category_id}", ...)  # 501
router.get("/", ...)               # 501
```

### topics.py — `TopicsRouter` (Stub)

Same pattern as categories — all 501.

### system.py — `SystemRouter`

```python
router = APIRouter(tags=["System"])

# Health (outside /api/v1)
health_router = APIRouter(prefix="/health")
health_router.get("/", ...)         # Full health check
health_router.get("/live", ...)     # Liveness probe
health_router.get("/ready", ...)    # Readiness probe

# Info (inside /api/v1)
info_router = APIRouter(prefix="/info")
info_router.get("/", ...)           # System info
```

## 3. Router Composition (main.py)

```python
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Shorts System — Ingestion API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── API v1 routes ──
    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(sources_router)
    api_v1.include_router(feeds_router, prefix="/feeds")  # flat feed routes
    api_v1.include_router(articles_router)
    api_v1.include_router(categories_router)
    api_v1.include_router(topics_router)
    api_v1.include_router(info_router)

    app.include_router(api_v1)

    # ── Health (outside /api/v1) ──
    app.include_router(health_router)

    # ── Middleware (order matters — first added = outermost) ──
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(AccessLogMiddleware)

    # ── Exception handlers ──
    register_exception_handlers(app)

    return app
```

## 4. Middleware Ordering

FastAPI middleware executes in REVERSE order of `add_middleware` calls:

```
Request enters
    ↓
1. AccessLogMiddleware     (outermost — logs everything)
    ↓
2. TimingMiddleware        (starts timer)
    ↓
3. CorrelationIDMiddleware (propagates X-Correlation-ID)
    ↓
4. RequestIDMiddleware     (ensures X-Request-ID exists)
    ↓
5. Router handler          (business logic)
    ↓
4. RequestIDMiddleware     (adds request_id to response)
    ↓
3. CorrelationIDMiddleware (adds correlation_id to response)
    ↓
2. TimingMiddleware        (logs duration)
    ↓
1. AccessLogMiddleware     (logs response status)
```

## 5. Route Parameter Conventions

| Convention | Example | Notes |
|-----------|---------|-------|
| Path IDs | `{source_id}` | UUID strings, validated as UUID in Pydantic |
| Query pagination | `?page=1&page_size=50` | Defaults: page=1, page_size=20, max=100 |
| Nested resources | `/sources/{id}/feeds` | Scoped listing |
| Flat resources | `/feeds/{id}` | Direct access by ID |
| State actions | `POST /{id}/activate` | POST (not PATCH) — they're commands |
| Relationship actions | `POST /{id}/categories` | POST with body containing target ID |

## 6. Naming Rules

| Operation | HTTP Method | URL Pattern | Examples |
|-----------|------------|-------------|----------|
| Create | POST | `/resources` | `POST /sources` |
| Update (full) | PUT | `/resources/{id}` | `PUT /sources/{id}` |
| Update (partial) | PATCH | `/resources/{id}` | `PATCH /sources/{id}` |
| Delete/Disable | DELETE | `/resources/{id}` | `DELETE /sources/{id}` |
| Find | GET | `/resources/{id}` | `GET /sources/{id}` |
| List | GET | `/resources` | `GET /sources` |
| State action | POST | `/resources/{id}/action` | `POST /sources/{id}/activate` |
| Assign relationship | POST | `/resources/{id}/relationship` | `POST /sources/{id}/categories` |

---

*See also: `api-design.md`, `composition-root.md`, `observability.md`*
