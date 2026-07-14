# Design: API Contract — Complete Endpoint Reference

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D4 (API-First), D5 (Ubiquitous Language), D6 (Versioning), D9 (OpenAPI as Contract)

---

## 1. API Surface Overview

**Base URL**: `/api/v1`
**Content-Type**: `application/json`
**Versioning**: URL path prefix (`/api/v1/`)

| Aggregate | Operations | Total |
|-----------|-----------|-------|
| Sources | 11 (CRUD + state + assign) | 11 |
| Feeds | 11 (CRUD + state + sync + failure + assign) | 11 |
| Articles | 3 (create + find + list) | 3 |
| System | 4 (health × 3 + info) | 4 |
| **Total** | | **29** |

> Note: Categories and Topics have NO Application Service yet. Their routers return `501 Not Implemented` stubs.

## 2. Global Conventions

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-Request-ID` | No | Client-generated request identifier. Auto-generated if absent. |
| `X-Correlation-ID` | No | Correlation ID for distributed tracing. Propagates through stack. |
| `Idempotency-Key` | No | For POST retry safety (see `idempotency-strategy.md`) |
| `Accept` | No | `application/json` (default) |

### Naming Conventions (W-02 Resolved)

| Operation | Endpoint Pattern | Command |
|-----------|-----------------|---------|
| Activate | `POST /api/v1/{resource}/{id}/activate` | Activate{Resource}Command |
| Deactivate | `POST /api/v1/{resource}/{id}/deactivate` | Deactivate{Resource}Command |
| Sync | `POST /api/v1/feeds/{id}/sync` | SyncFeedCommand |
| Assign Category | `POST /api/v1/{resource}/{id}/categories` | AssignCategoryTo{Resource}Command |
| Assign Topic | `POST /api/v1/{resource}/{id}/topics` | AssignTopicTo{Resource}Command |

> **Rationale**: "activate/deactivate" aligns with domain language (`ActivateFeedCommand`, `DeactivateFeedCommand`). "enable/disable" is UI language, not domain language. The API surface mirrors the Ubiquitous Language.

### Response Envelope

All responses follow:

```json
{
  "status": "success",
  "data": { ... },
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

Error responses follow RFC 9457 (see `exception-handling.md`):

```json
{
  "type": "about:blank",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Source 'abc-123' not found",
  "instance": "/api/v1/sources/abc-123",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

### Pagination (W-04 Resolved)

Request parameters:
```
GET /api/v1/sources?page=1&page_size=20&sort=name&order=asc
```

Response envelope:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  },
  "links": {
    "self": "/api/v1/sources?page=1&page_size=20",
    "next": "/api/v1/sources?page=2&page_size=20",
    "prev": null,
    "first": "/api/v1/sources?page=1&page_size=20",
    "last": "/api/v1/sources?page=8&page_size=20"
  }
}
```

Limits: `page_size` default=20, max=100.
Sorting: `sort` param (field name), `order` param (asc/desc).

## 3. Sources — 11 Endpoints

### POST /api/v1/sources — RegisterSource

**Summary**: Register a new news source

**Request**:
```json
{
  "name": "TechCrunch",
  "source_type": "RSS",
  "source_url": "https://techcrunch.com/feed/"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| name | string | ✅ | 1-200 chars, unique |
| source_type | enum | ✅ | RSS, API, SOCIAL_MEDIA, NEWSLETTER |
| source_url | string (URL) | ✅ | Valid URL format |

**Response 201**:
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "TechCrunch",
    "source_type": "RSS",
    "source_url": "https://techcrunch.com/feed/",
    "is_active": false,
    "categories": [],
    "topics": []
  }
}
```

**Errors**: 409 (duplicate name), 422 (validation), 500 (internal)

---

### PUT /api/v1/sources/{source_id} — UpdateSource

**Summary**: Full update of a news source

**Path**: `source_id: UUID string`

**Request**:
```json
{
  "name": "TechCrunch Updated",
  "source_type": "RSS",
  "source_url": "https://techcrunch.com/feed/v2/"
}
```

All fields optional (partial update semantics).

**Response 200**: SourceDetailDTO
**Errors**: 404 (not found), 409 (duplicate name), 422 (validation)

---

### PATCH /api/v1/sources/{source_id} — UpdateSource (partial)

Same as PUT — both support partial updates. PUT requires all fields present in schema, PATCH allows all-optional.

**Response 200**: SourceDetailDTO
**Errors**: 404, 409, 422

---

### DELETE /api/v1/sources/{source_id} — DeactivateSource

**Summary**: Deactivate a news source

**Request body** (required):
```json
{
  "reason": "Source no longer maintained"
}
```

**Response 200**: SourceDetailDTO with `is_active: false`
**Errors**: 404 (not found), 409 (has active feeds — AL-01)

---

### GET /api/v1/sources/{source_id} — FindSource

**Summary**: Get source details by ID

**Response 200**: SourceDetailDTO
**Errors**: 404

---

### GET /api/v1/sources — ListActiveSources

**Summary**: List all active sources

**Query params**: None (YAGNI)

**Response 200**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "...",
      "name": "TechCrunch",
      "source_type": "RSS",
      "source_url": "...",
      "is_active": true
    }
  ],
  "meta": { "total": 5 }
}
```

---

### POST /api/v1/sources/{source_id}/activate — ActivateSource

**Summary**: Activate a source for ingestion

**Business Rule**: AL-02 — requires at least one active feed

**Request body**: Empty `{}`

**Response 200**: SourceDetailDTO with `is_active: true`
**Errors**: 404, 409 (no active feeds)

---

### POST /api/v1/sources/{source_id}/deactivate — DeactivateSource

**Summary**: Deactivate a source

**Business Rule**: AL-01 — cannot deactivate if has active feeds

**Request body**: `{ "reason": "..." }`

**Response 200**: SourceDetailDTO with `is_active: false`
**Errors**: 404, 409 (has active feeds)

---

### POST /api/v1/sources/{source_id}/categories — AssignCategoryToSource

**Summary**: Assign a category to a source

**Request body**:
```json
{
  "category_id": "550e8400-..."
}
```

**Response 200**: SourceDetailDTO (updated categories)
**Errors**: 404 (source or category not found)

---

### POST /api/v1/sources/{source_id}/topics — AssignTopicToSource

**Summary**: Assign a topic to a source

**Request body**:
```json
{
  "topic_id": "550e8400-..."
}
```

**Response 200**: SourceDetailDTO (updated topics)
**Errors**: 404 (source or topic not found)

## 4. Feeds — 11 Endpoints

### POST /api/v1/sources/{source_id}/feeds — RegisterFeed

**Summary**: Register a new feed under a source

**Request**:
```json
{
  "url": "https://techcrunch.com/category/ai/feed/",
  "label": "TechCrunch AI",
  "language": "en",
  "sync_mode": "PULL",
  "sync_interval_minutes": 30,
  "sync_max_retries": 3,
  "categories": ["550e8400-..."],
  "topics": ["660e8400-..."]
}
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| url | string (URL) | ✅ | — |
| label | string | ✅ | — |
| language | string (ISO 639-1) | ✅ | — |
| sync_mode | enum | No | PULL |
| sync_interval_minutes | int | No | 30 |
| sync_max_retries | int | No | 3 |
| categories | UUID[] | No | [] |
| topics | UUID[] | No | [] |

**Response 201**: FeedDetailDTO
**Errors**: 404 (source not found), 409 (duplicate URL), 422 (validation), 409 (source inactive — AL-04)

---

### PUT /api/v1/feeds/{feed_id} — UpdateFeed

**Summary**: Update feed configuration

All fields optional (partial update).

**Response 200**: FeedDetailDTO
**Errors**: 404, 409, 422

---

### PATCH /api/v1/feeds/{feed_id} — UpdateFeed (partial)

Same as PUT — both support partial updates.

---

### DELETE /api/v1/feeds/{feed_id} — DeactivateFeed

**Summary**: Deactivate a feed

**Request body**: `{ "reason": "Maintenance" }`

**Response 200**: FeedDetailDTO with `is_active: false`
**Errors**: 404

---

### GET /api/v1/feeds/{feed_id} — FindFeed

**Summary**: Get feed details by ID

**Response 200**: FeedDetailDTO
**Errors**: 404

---

### GET /api/v1/sources/{source_id}/feeds — ListFeeds

**Summary**: List feeds for a source

**Query params**: `?page=1&page_size=50`

**Response 200**: Paginated FeedSummaryDTO list
**Errors**: 404 (source not found)

---

### POST /api/v1/feeds/{feed_id}/activate — ActivateFeed

**Summary**: Reactivate a paused feed

**Request body**: Empty `{}`

**Response 200**: FeedDetailDTO with `is_active: true`
**Errors**: 404

---

### POST /api/v1/feeds/{feed_id}/deactivate — DeactivateFeed

**Summary**: Deactivate a feed

**Request body**: `{ "reason": "..." }`

**Response 200**: FeedDetailDTO
**Errors**: 404

---

### POST /api/v1/feeds/{feed_id}/sync — RecordCollection

**Summary**: Record a successful collection

**Request body**:
```json
{
  "count": 15,
  "batch_id": "770e8400-..."
}
```

**Response 200**: FeedDetailDTO
**Errors**: 404

---

### POST /api/v1/feeds/{feed_id}/failure — RecordFeedCollectionFailure

**Summary**: Record a failed collection attempt for a feed

**Description**: Internal endpoint used by collectors to report collection failures. Updates feed status and creates an error record.

**Request body**:
```json
{
  "error": "Connection timeout after 30s",
  "occurred_at": "2026-07-13T10:30:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| error | string | ✅ | Error description |
| occurred_at | datetime (ISO 8601) | ✅ | When the failure occurred |

**Response 200**: FeedDetailDTO with updated status
**Errors**: 404 (feed not found), 500 (internal error)

**Idempotency**: Yes — same failure recorded twice returns same result
**Tags**: Feeds (Internal)
**Auth**: Internal only (API key required)

---

### POST /api/v1/feeds/{feed_id}/categories — AssignCategoryToFeed

**Request body**: `{ "category_id": "..." }`
**Response 200**: FeedDetailDTO
**Errors**: 404

---

### POST /api/v1/feeds/{feed_id}/topics — AssignTopicToFeed

**Request body**: `{ "topic_id": "..." }`
**Response 200**: FeedDetailDTO
**Errors**: 404

## 5. Articles — 3 Endpoints

### POST /api/v1/feeds/{feed_id}/articles — CreateArticle

**Summary**: Create a raw article from a feed

**Request**:
```json
{
  "external_id": "tc-2026-001",
  "content_hash": "a1b2c3d4e5f6...",
  "title": "AI Breakthrough in 2026",
  "url": "https://techcrunch.com/2026/07/13/ai-breakthrough/",
  "author": "Jane Doe",
  "language": "en",
  "published_at": "2026-07-13T10:00:00Z",
  "content_preview": "A brief summary..."
}
```

**Response 201**: RawArticleDetailDTO
**Errors**: 404 (feed not found), 409 (duplicate URL or hash), 422

---

### GET /api/v1/articles/{article_id} — FindArticle

**Response 200**: RawArticleDetailDTO
**Errors**: 404

---

### GET /api/v1/feeds/{feed_id}/articles — ListArticles

**Query params**: `?page=1&page_size=50`
**Response 200**: Paginated RawArticleSummaryDTO list
**Errors**: 404 (feed not found)

## 6. Categories — 5 Endpoints (Stubs)

All return `501 Not Implemented` until CategoryService is created.

- `POST /api/v1/categories` — CreateCategory
- `PUT /api/v1/categories/{category_id}` — UpdateCategory
- `DELETE /api/v1/categories/{category_id}` — DeleteCategory
- `GET /api/v1/categories/{category_id}` — FindCategory
- `GET /api/v1/categories` — ListCategories

## 7. Topics — 5 Endpoints (Stubs)

All return `501 Not Implemented` until TopicService is created.

- `POST /api/v1/topics` — CreateTopic
- `PUT /api/v1/topics/{topic_id}` — UpdateTopic
- `DELETE /api/v1/topics/{topic_id}` — DeleteTopic
- `GET /api/v1/topics/{topic_id}` — FindTopic
- `GET /api/v1/topics` — ListTopics

## 8. System — 4 Endpoints

### GET /health — HealthCheck

**Summary**: Full health check

**Response 200**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-07-13T14:00:00Z",
  "checks": {
    "database": { "status": "healthy", "latency_ms": 2 },
    "event_publisher": { "status": "healthy" }
  }
}
```

### GET /health/live — LivenessProbe

**Summary**: Is the process alive?

**Response 200**: `{ "status": "alive" }`

### GET /health/ready — ReadinessProbe

**Summary**: Is the service ready to accept traffic?

Checks database connectivity, returns 503 if not ready.

### GET /api/v1/info — SystemInfo

**Summary**: System information

**Response 200**:
```json
{
  "name": "AI Shorts System — Ingestion BC",
  "version": "1.0.0",
  "api_version": "v1",
  "environment": "development"
}
```

## 9. OpenAPI Tags

| Tag | Description |
|-----|-------------|
| Sources | News source management |
| Feeds | Feed management and synchronization |
| Articles | Raw article ingestion |
| Categories | Category management (stub) |
| Topics | Topic management (stub) |
| System | Health checks and system info |

---

*See also: `routing-strategy.md`, `serialization.md`, `idempotency-strategy.md`, `exception-handling.md`*
