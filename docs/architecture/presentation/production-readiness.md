# Production Readiness Checklist — Ingestion API

**Sprint**: 6.4 — Observability & Operations Hardening
**Date**: 2026-07-14
**Status**: REVIEW COMPLETE

---

## Configuration

- [x] **PASS**: All settings from environment variables
  - Evidence: `src/ingestion/presentation/config.py:44-50` — `SettingsConfigDict(env_prefix="AI_SHORTS_")`
  - Test: `tests/ingestion/presentation/test_config.py:68-99` — 4 tests verify env override

- [x] **PASS**: No hardcoded secrets in code
  - Evidence: `config.py:76` — `SECRET_KEY` has a placeholder default `"change-me-in-production"`, loaded from `AI_SHORTS_SECRET_KEY` env var
  - ⚠️ **Warning**: Default value is insecure. No startup validation that it was changed in production.

- [x] **PASS**: Defaults suitable for production
  - Evidence: `config.py:55-81` — `DEBUG=False`, `LOG_LEVEL="INFO"`, `LOG_FORMAT="json"`, `HOST="0.0.0.0"`, `PORT=8000`
  - Test: `tests/ingestion/presentation/test_config.py:21-63` — 2 tests verify all defaults

- [ ] **FAIL**: SECRET_KEY configured and secure
  - Evidence: `config.py:76` — Default is `"change-me-in-production"`. No validation that it's been changed when `ENVIRONMENT=production`.
  - **Recommendation**: Add startup check: `if ENVIRONMENT == "production" and SECRET_KEY == "change-me-in-production": raise RuntimeError`

---

## Logging

- [x] **PASS**: JSON format for production
  - Evidence: `src/ingestion/presentation/logging_config.py:44-69` — `JSONFormatter` produces single-line JSON with timestamp, level, message, logger, request_id, correlation_id
  - Test: `tests/ingestion/presentation/test_logging.py:71-131` — 3 tests verify JSON output

- [x] **PASS**: Request context (request_id, correlation_id) in logs
  - Evidence: `logging_config.py:23-41` — `RequestContextFilter` injects `request_id` and `correlation_id` into all log records
  - Test: `tests/ingestion/presentation/test_logging.py:133-173` — 2 tests verify injection

- [x] **PASS**: No sensitive data in logs
  - Evidence: No request body or response body logging. Only metadata (request_id, correlation_id, path, method).
  - ⚠️ **Note**: Exception handlers log error messages but not full stacktraces in the response body.

- [x] **PASS**: Appropriate log levels
  - Evidence: Exception handlers use `logger.error()` for handled exceptions and `logger.exception()` for unhandled. No `DEBUG` or `WARNING` noise in normal operation.
  - Test: `tests/ingestion/presentation/test_exceptions.py` — verifies exception handlers are called

---

## Health

- [x] **PASS**: /health/live endpoint responding
  - Evidence: `src/ingestion/presentation/health.py:27-33` — Returns `200 {"status": "alive"}`
  - Test: `tests/ingestion/presentation/test_health.py:79-84` — `test_liveness_returns_200`

- [x] **PASS**: /health/ready checks DB connectivity
  - Evidence: `health.py:36-56` — Executes `SELECT 1`, returns `200 {"status": "ready"}` or `503 {"status": "not_ready"}`
  - Test: `tests/ingestion/presentation/test_health.py:90-108` — 2 tests: healthy DB, unhealthy DB

- [x] **PASS**: Health endpoints outside /api/v1
  - Evidence: `src/ingestion/presentation/app.py:125` — `app.include_router(health_router)` without prefix
  - Test: `tests/ingestion/presentation/test_openapi.py:27-33` — Verifies `/health/live` and `/health/ready` in schema paths

---

## Errors

- [x] **PASS**: RFC 9457 Problem Details for all errors
  - Evidence: `src/ingestion/presentation/exceptions.py:49-67` — `ProblemDetail` Pydantic model with `type`, `title`, `status`, `detail`, `instance`, `error_code`
  - Test: `tests/ingestion/presentation/test_sources.py:500-543` — Problem Details format + content-type

- [x] **PASS**: Content-Type: application/problem+json
  - Evidence: `exceptions.py:98-102` — `media_type="application/problem+json"` on all `problem_response()` calls
  - Test: `tests/ingestion/presentation/test_exceptions.py:101-104` — Verifies content-type header

- [x] **PASS**: No stacktrace in 4xx responses
  - Evidence: 4xx errors (404, 409, 422) are handled by router helpers (`_error_response()` in `routers/sources.py:63-75`) which call `problem_response()` directly without logging. Stacktraces are NOT included in the response body.
  - Test: `tests/ingestion/presentation/test_sources.py:504-523` — 404 Problem Details body verified (no stacktrace)

- [x] **PASS**: Stacktrace logged for 5xx errors
  - Evidence: All exception handlers use `exc_info=True`:
    - `exceptions.py:208-216` — PersistenceError → `logger.error(..., exc_info=True)`
    - `exceptions.py:228-236` — InfrastructureError → `logger.error(..., exc_info=True)`
    - `exceptions.py:255-265` — FoundationError → `logger.error(..., exc_info=True)`
    - `exceptions.py:279-286` — Generic Exception → `logger.exception(...)` (implicit exc_info=True)
    - `middleware.py:110-116` — RecoveryMiddleware → `logger.exception(...)`

---

## Observability

- [x] **PASS**: X-Request-ID generated/preserved
  - Evidence: `src/ingestion/presentation/middleware.py:44-51` — `RequestIDMiddleware` generates UUID v4 or preserves client-provided ID
  - Test: `tests/ingestion/presentation/test_middleware.py:43-68` — 3 tests

- [x] **PASS**: X-Correlation-ID propagated
  - Evidence: `middleware.py:65-75` — `CorrelationIDMiddleware` reads or derives from request_id
  - Test: `tests/ingestion/presentation/test_middleware.py:70-96` — 3 tests

- [x] **PASS**: X-Request-Duration header present
  - Evidence: `middleware.py:86-94` — `TimingMiddleware` measures with `time.perf_counter()`, formats as `X.XXms`
  - Test: `tests/ingestion/presentation/test_middleware.py:98-122` — 3 tests (header, format, positive)

- [x] **PASS**: Request context in structured logs
  - Evidence: `logging_config.py:23-41` — `RequestContextFilter` injects `request_id` and `correlation_id` into all log records
  - Test: `tests/ingestion/presentation/test_logging.py:133-173` — 2 tests

---

## Security Headers

- [x] **PASS**: CORS configured
  - Evidence: `src/ingestion/presentation/app.py:135-141` — `CORSMiddleware` added when `CORS_ORIGINS` is non-empty
  - Test: `tests/ingestion/presentation/test_config.py:92-99` — Verifies CORS from env
  - ⚠️ **Note**: CORS is conditionally added (only when `CORS_ORIGINS` is set). Default is `["http://localhost:3000"]`.

- [ ] **FAIL**: TrustedHost middleware
  - Evidence: Not implemented. No `TrustedHostMiddleware` in `app.py`.
  - **Recommendation**: Add `TrustedHostMiddleware` for production to prevent Host header attacks.
  - **Sprint**: Planned for Sprint 6.5

- [ ] **FAIL**: Security headers (HSTS, X-Content-Type-Options, etc.)
  - Evidence: Not implemented. No `SecurityHeadersMiddleware` in `app.py`.
  - **Recommendation**: Add security headers middleware for production.
  - **Sprint**: Planned for Sprint 6.5

---

## OpenAPI

- [x] **PASS**: Schema generated correctly
  - Evidence: `tests/ingestion/presentation/test_openapi.py:18-25` — Verifies title starts with "AI Shorts System", version "1.0.0"

- [x] **PASS**: All endpoints documented
  - Evidence: Tests verify all expected paths in schema:
    - Sources: `test_sources.py:560-586` — 8 endpoints verified
    - Feeds: `test_feeds.py:703-754` — 10 endpoints verified
    - Articles: `test_articles.py:315-347` — 3 endpoints verified
    - Health: `test_openapi.py:27-33` — 2 endpoints verified

- [x] **PASS**: Tags organized by resource
  - Evidence: Router definitions:
    - `routers/sources.py:55` — `APIRouter(tags=["Sources"])`
    - `routers/feeds.py` — `APIRouter(tags=["Feeds"])`
    - `routers/articles.py` — `APIRouter(tags=["Articles"])`
    - `routers/categories.py` — `APIRouter(tags=["Categories"])`
    - `routers/topics.py` — `APIRouter(tags=["Topics"])`
    - `health.py:24` — `APIRouter(tags=["System"])`

- [x] **PASS**: operationId for all operations
  - Evidence: FastAPI auto-generates operationId from function names (e.g., `create_source`, `list_sources`, `get_source`). Verified via OpenAPI schema tests.

- [x] **PASS**: Schemas for request/response models
  - Evidence: All endpoints use Pydantic models for request bodies and response models:
    - Sources: `RegisterSourceRequest`, `SourceDetailResponse`, `PaginatedSourcesResponse`, etc.
    - Feeds: `RegisterFeedRequest`, `FeedDetailResponse`, etc.
    - Articles: `CreateArticleRequest`, `RawArticleDetailResponse`, etc.

---

## Dependency Injection

- [x] **PASS**: All dependencies properly provided
  - Evidence: `src/ingestion/presentation/dependencies.py` — 11 providers:
    - Singletons: `get_settings`, `get_session_factory`
    - Scoped: `get_uow` (generator, auto-rollback)
    - Transient: `get_event_publisher`, `get_clock`, `get_uuid_provider`
    - Services: `get_source_service`, `get_feed_service`, `get_article_service`, `get_category_service`, `get_topic_service`
  - Test: `tests/ingestion/presentation/test_dependencies.py` — 3 tests: settings, session_factory, UoW lifecycle

- [x] **PASS**: DI overrides work for testing
  - Evidence: Every router test file uses `app.dependency_overrides[get_*_service]` to inject mocks:
    - `test_sources.py:132-133` — `dependency_overrides[get_source_service]`
    - `test_feeds.py:150-151` — `dependency_overrides[get_feed_service]`
    - `test_articles.py:104-105` — `dependency_overrides[get_article_service]`
    - `test_health.py:93-94` — `dependency_overrides[get_session_factory]`

- [x] **PASS**: No circular dependencies
  - Evidence: DI graph is a clean tree: Settings → Engine → SessionFactory → UoW → Repos → Services. No cycles.

---

## UoW Lifecycle

- [x] **PASS**: Unit of Work created per request
  - Evidence: `dependencies.py:88-112` — `get_uow()` is a generator (FastAPI yield-based DI), creates `SQLAlchemyUnitOfWork` per request

- [x] **PASS**: Committed on success
  - Evidence: Services call `uow.commit()` explicitly (e.g., in `SourceService.execute_register_source`). The `with uow:` block in `get_uow` handles the lifecycle.
  - UoW commit: `unit_of_work.py:98-133` — `commit()` calls `session.commit()`, collects events, publishes

- [x] **PASS**: Rolled back on failure
  - Evidence: `unit_of_work.py:83-94` — `__exit__` calls `rollback()` if `exc_type is not None`, then `close()`
  - Test: `tests/ingestion/presentation/test_dependencies.py:88-127` — `test_uow_lifecycle` verifies `__exit__` is called

---

## Middleware Ordering

- [x] **PASS**: Recovery (outermost)
  - Evidence: `app.py:116` — `app.add_middleware(RecoveryMiddleware)` — first `add_middleware` = last in stack = outermost execution

- [x] **PASS**: Timing
  - Evidence: `app.py:117` — `app.add_middleware(TimingMiddleware)` — second

- [x] **PASS**: CorrelationID
  - Evidence: `app.py:118` — `app.add_middleware(CorrelationIDMiddleware)` — third

- [x] **PASS**: RequestID (innermost)
  - Evidence: `app.py:119` — `app.add_middleware(RequestIDMiddleware)` — last `add_middleware` = innermost
  - Test: `tests/ingestion/presentation/test_app.py:95-117` — `test_middleware_order` verifies `request_idx < correlation_idx < timing_idx < recovery_idx`

---

## Versioning

- [x] **PASS**: API version in URL (/api/v1)
  - Evidence: `app.py:128-132` — All routers included with `prefix="/api/v1"`
  - Routes: `/api/v1/sources`, `/api/v1/feeds`, `/api/v1/articles`, `/api/v1/categories`, `/api/v1/topics`

- [x] **PASS**: OpenAPI version matches
  - Evidence: `config.py:54` — `openapi_version: str = "1.0.0"`, used in `app.title` and `app.version`
  - Test: `tests/ingestion/presentation/test_openapi.py:18-25` — Verifies `info.version == "1.0.0"`

- [x] **PASS**: Backward compatibility maintained
  - Evidence: All endpoints are additive (new resources added, no breaking changes to existing contracts). Health endpoints are outside `/api/v1`.

---

## Summary

| Category | Pass | Fail | Total |
|----------|------|------|-------|
| Configuration | 3 | 1 | 4 |
| Logging | 4 | 0 | 4 |
| Health | 3 | 0 | 3 |
| Errors | 4 | 0 | 4 |
| Observability | 4 | 0 | 4 |
| Security Headers | 1 | 2 | 3 |
| OpenAPI | 5 | 0 | 5 |
| Dependency Injection | 3 | 0 | 3 |
| UoW Lifecycle | 3 | 0 | 3 |
| Middleware Ordering | 4 | 0 | 4 |
| Versioning | 3 | 0 | 3 |
| **TOTAL** | **37** | **3** | **40** |

### Overall Assessment: 37/40 PASS (92.5%)

### FAIL Items

1. **SECRET_KEY validation**: No startup check that SECRET_KEY has been changed from default in production. **Action**: Add validation in `create_app()`.

2. **TrustedHost middleware**: Not implemented. **Action**: Sprint 6.5.

3. **Security headers**: Not implemented. **Action**: Sprint 6.5.

### Warnings (Non-blocking)

1. **AccessLogMiddleware not implemented**: The design doc specified an access log middleware logging every request. Not implemented. All request context is available via `request.state` and the `RequestContextFilter` injects it into logs, but there's no middleware that logs every request's method, path, status, and duration.

2. **No file logging**: Only stdout via `StreamHandler`. No file rotation, no log shipping.

3. **Duration not in log records**: `duration_ms` is available on `request.state` but not injected into log records by `RequestContextFilter`.
