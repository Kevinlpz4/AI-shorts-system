# Observability Audit — Ingestion API

**Sprint**: 6.4 — Observability & Operations Hardening
**Date**: 2026-07-14
**Status**: AUDIT COMPLETE
**Frozen layers**: Domain, Application, Persistence, API contract

---

## 1. Request Tracing

### 1.1 X-Request-ID

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/middleware.py:33-51` — `RequestIDMiddleware` |
| **Behavior** | Reads `X-Request-ID` from incoming request header. If absent, generates UUID v4. Stores on `request.state.request_id`. Sets on response header. |
| **UUID format** | `str(uuid.uuid4())` — standard UUID v4 |
| **Preservation** | Client-provided IDs are preserved exactly (no validation beyond string type) |
| **Test coverage** | `tests/ingestion/presentation/test_middleware.py:40-68` — 3 tests: auto-generate, preserve client ID, response header present |

**Test methods:**
- `TestRequestIDMiddleware::test_auto_generates_request_id` — verifies UUID format
- `TestRequestIDMiddleware::test_preserves_client_request_id` — verifies client ID passthrough
- `TestRequestIDMiddleware::test_request_id_in_response_header` — verifies header always present

**Configuration**: None — always active.

**Known limitations**:
- No UUID format validation on client-provided IDs (any string accepted)
- No length limit on client-provided IDs

### 1.2 X-Correlation-ID

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/middleware.py:54-75` — `CorrelationIDMiddleware` |
| **Behavior** | Reads `X-Correlation-ID` from incoming request header. If absent, derives from `request.state.request_id`. Stores on `request.state.correlation_id`. Sets on response header. |
| **Test coverage** | `tests/ingestion/presentation/test_middleware.py:70-96` — 3 tests: fallback to request_id, preserve client correlation_id, response header present |

**Test methods:**
- `TestCorrelationIDMiddleware::test_uses_request_id_when_no_correlation_id`
- `TestCorrelationIDMiddleware::test_preserves_client_correlation_id`
- `TestCorrelationIDMiddleware::test_correlation_id_in_response_header`

**Configuration**: None — always active.

**Known limitations**:
- Falls back silently to request_id — no way to distinguish "client didn't send" from "same as request_id"
- Correlation ID is not propagated to downstream services (no external HTTP calls from this API)

### 1.3 Request Context Propagation

| Aspect | Detail |
|--------|--------|
| **Implementation** | Both IDs stored on `request.state` (Starlette State object) |
| **Availability** | Available in all handlers via `request.state.request_id` and `request.state.correlation_id` |
| **Logging injection** | `RequestContextFilter` in `src/ingestion/presentation/logging_config.py:23-41` adds `record.request_id` and `record.correlation_id` to all log records |
| **Test coverage** | `tests/ingestion/presentation/test_logging.py:133-173` — 2 tests: adds defaults, preserves existing |

---

## 2. Timing

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/middleware.py:78-94` — `TimingMiddleware` |
| **Behavior** | Measures time from before to after handler execution using `time.perf_counter()`. Sets `X-Request-Duration` header (milliseconds, 2 decimal places). Stores `request.state.duration_ms` as a float. |
| **Header format** | `X.XXms` (e.g., `1.23ms`) |
| **Test coverage** | `tests/ingestion/presentation/test_middleware.py:98-122` — 3 tests: header present, format matches regex `^\d+\.\d{2}ms$`, value is positive |

**Test methods:**
- `TestTimingMiddleware::test_timing_header_present`
- `TestTimingMiddleware::test_timing_header_format`
- `TestTimingMiddleware::test_timing_is_positive`

**Configuration**: None — always active.

**Known limitations**:
- Measures total middleware stack time, not just handler time (includes all inner middleware)
- No separate handler-only timing
- No server processing time vs. network time distinction

---

## 3. Structured Logging

### 3.1 Configuration

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/logging_config.py:72-97` — `setup_logging()` |
| **Called from** | `src/ingestion/presentation/app.py:77-80` — during `create_app()` |
| **Configuration source** | `Settings.LOG_LEVEL` (default: `"INFO"`) and `Settings.LOG_FORMAT` (default: `"json"`) |
| **Test coverage** | `tests/ingestion/presentation/test_logging.py:26-66` — 5 tests: root level, debug level, JSON format, text format, filter attached |

### 3.2 JSON Formatter (Production)

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/logging_config.py:44-69` — `JSONFormatter` |
| **Fields** | `timestamp`, `level`, `message`, `logger`, `request_id`, `correlation_id` |
| **Output** | Single valid JSON line per log record |
| **Test coverage** | `tests/ingestion/presentation/test_logging.py:68-131` — 3 tests: valid JSON with required fields, includes context fields, defaults for missing context |

**Example output:**
```json
{"timestamp": "2026-07-14T20:15:00,123", "level": "INFO", "message": "Request processed", "logger": "ingestion.presentation.middleware", "request_id": "abc-123", "correlation_id": "abc-123"}
```

### 3.3 Text Formatter (Development)

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/logging_config.py:91-95` — `logging.Formatter` |
| **Format** | `%(asctime)s [%(levelname)s] %(name)s: %(message)s` |

### 3.4 RequestContextFilter

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/logging_config.py:23-41` — `RequestContextFilter` |
| **Behavior** | Adds `request_id` and `correlation_id` to every log record. Defaults to `"-"` when not in a request context. Never filters out records (always returns `True`). |
| **Test coverage** | `tests/ingestion/presentation/test_logging.py:133-173` — 2 tests: adds defaults, preserves existing values |

**Configuration**: Via `AI_SHORTS_LOG_LEVEL` and `AI_SHORTS_LOG_FORMAT` environment variables.

**Known limitations**:
- No `duration_ms` field in log records (only in response header and `request.state`)
- No `method`, `path`, `status_code` fields in logs (not an access log middleware)
- No request body logging
- No response body logging
- Single handler only (no file rotation, no log shipping)

---

## 4. Exception Handling

### 4.1 Problem Details Model (RFC 9457)

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/exceptions.py:49-67` — `ProblemDetail` (Pydantic model) |
| **Fields** | `type`, `title`, `status`, `detail`, `instance`, `error_code` (custom extension) |
| **Content-Type** | `application/problem+json` |
| **Helper** | `problem_response()` at line 69-102 creates `JSONResponse` with correct media type |

### 4.2 Error Code → HTTP Status Mappers

| Aspect | Detail |
|--------|--------|
| **Domain mapper** | `src/ingestion/presentation/exceptions.py:122-147` — `_DOMAIN_CODE_TO_STATUS` (18 codes) |
| **Application mapper** | `src/ingestion/presentation/exceptions.py:110-117` — `_APP_CODE_TO_STATUS` (6 codes) |
| **Lookup order** | Domain codes first → Application codes → fallback 500 |
| **Implementation** | `map_error_code_to_status()` at line 150-169 |
| **Test coverage** | `tests/ingestion/presentation/test_exceptions.py:56-82` — 6 tests covering 404, 409, 422, application codes, unknown fallback |

**Domain code coverage:**
| Category | Codes | HTTP Status |
|----------|-------|-------------|
| Not Found | `NEWS_SOURCE_NOT_FOUND`, `FEED_NOT_FOUND`, `RAW_ARTICLE_NOT_FOUND`, `CATEGORY_NOT_FOUND`, `TOPIC_NOT_FOUND` | 404 |
| Conflicts | `DUPLICATE_NEWS_SOURCE`, `DUPLICATE_FEED_URL`, `DUPLICATE_ARTICLE`, `NEWS_SOURCE_INACTIVE`, `FEED_INACTIVE`, `HAS_ACTIVE_FEEDS`, `FEED_ALREADY_PAUSED`, `FEED_MAX_RETRIES_EXCEEDED` | 409 |
| Validation | `INVALID_SOURCE_URL`, `INVALID_ARTICLE_URL`, `INVALID_LANGUAGE`, `INVALID_SYNC_POLICY`, `VALIDATION_ERROR`, `CYCLE_DETECTED` | 422 |
| State | `INVALID_STATE` | 500 |

### 4.3 Exception Handlers

| Exception Type | Handler Location | HTTP Status | Problem Type URI |
|---------------|-----------------|-------------|------------------|
| `PersistenceError` | `exceptions.py:203-223` | 503 | `https://api.ai-shorts.dev/errors/service-unavailable` |
| `InfrastructureError` | `exceptions.py:225-245` | 503 | `https://api.ai-shorts.dev/errors/service-unavailable` |
| `FoundationError` | `exceptions.py:247-272` | 500 | `https://api.ai-shorts.dev/errors/internal-error` |
| `Exception` (generic) | `exceptions.py:274-293` | 500 | `about:blank` |

**Test coverage:**
- `tests/ingestion/presentation/test_exceptions.py:87-105` — PersistenceError → 503, content-type
- `tests/ingestion/presentation/test_exceptions.py:107-118` — FoundationError → 500
- `tests/ingestion/presentation/test_exceptions.py:120-131` — Generic Exception → 500

**Stacktrace logging:**
- All exception handlers use `exc_info=True` (logs stacktrace)
- `PersistenceError`: `logger.error(..., exc_info=True)` (line 208-216)
- `InfrastructureError`: `logger.error(..., exc_info=True)` (line 228-236)
- `FoundationError`: `logger.error(..., exc_info=True)` (line 255-265)
- Generic: `logger.exception(...)` (implicit exc_info=True, line 279-286)
- `RecoveryMiddleware`: `logger.exception(...)` (line 110-116)

**Known limitations**:
- No stacktrace suppression for 4xx errors (handled by Pydantic/FastAPI before exception handlers)
- No distinction between "expected" errors (domain validation) and "unexpected" errors in logging
- No error correlation IDs (relies on request-level correlation)

### 4.4 Recovery Middleware (Last Resort)

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/middleware.py:97-128` — `RecoveryMiddleware` |
| **Behavior** | Catches ALL unhandled exceptions (including from other middleware). Returns 500 Problem Details. Logs with `logger.exception()`. |
| **Test coverage** | `tests/ingestion/presentation/test_middleware.py:124-150` — 3 tests: catches exception, returns Problem Details format, includes instance URL |

---

## 5. Health Endpoints

### 5.1 Liveness Probe

| Aspect | Detail |
|--------|--------|
| **Endpoint** | `GET /health/live` |
| **Implementation** | `src/ingestion/presentation/health.py:27-33` |
| **Response** | Always `200 {"status": "alive"}` |
| **Test coverage** | `tests/ingestion/presentation/test_health.py:76-84` — 1 test: returns 200 with alive status |
| **Dependencies** | None — no DI, no DB check |

### 5.2 Readiness Probe

| Aspect | Detail |
|--------|--------|
| **Endpoint** | `GET /health/ready` |
| **Implementation** | `src/ingestion/presentation/health.py:36-56` |
| **Response (healthy)** | `200 {"status": "ready"}` |
| **Response (unhealthy)** | `503 {"status": "not_ready"}` |
| **DB check** | `SELECT 1` via SQLAlchemy session |
| **Test coverage** | `tests/ingestion/presentation/test_health.py:87-108` — 2 tests: healthy DB, unhealthy DB |
| **Dependencies** | `get_session_factory` (DI, from `app.state.session_factory`) |

**Test methods:**
- `TestReadiness::test_readiness_healthy_db` — mock returns success
- `TestReadiness::test_readiness_unhealthy_db` — mock raises exception

**Configuration**: None — always active.

**Known limitations**:
- Only checks DB connectivity — no cache, external service, or disk space checks
- Health endpoints are outside `/api/v1` prefix (intentional — standard k8s convention)
- No version info in health response

---

## 6. Middleware Order

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/app.py:116-119` — `add_middleware()` calls |
| **Execution order** | Recovery (outermost) → Timing → CorrelationID → RequestID (innermost) → Handler |
| **Registration** | `app.py:116`: Recovery, `app.py:117`: Timing, `app.py:118`: CorrelationID, `app.py:119`: RequestID |
| **Test coverage** | `tests/ingestion/presentation/test_app.py:81-117` — 2 tests: all 4 middleware registered, correct execution order |

**Test methods:**
- `TestAppMiddleware::test_middleware_registered` — verifies all 4 class names present
- `TestAppMiddleware::test_middleware_order` — verifies `request_idx < correlation_idx < timing_idx < recovery_idx`

**Design rationale**:
- Recovery outermost: catches exceptions from ALL other middleware
- Timing second: measures total time including other middleware
- CorrelationID third: needs request_id from innermost middleware
- RequestID innermost: first to set request context

---

## 7. Configuration

| Aspect | Detail |
|--------|--------|
| **Implementation** | `src/ingestion/presentation/config.py:21-81` — `Settings` (pydantic-settings) |
| **Env prefix** | `AI_SHORTS_` |
| **Test coverage** | `tests/ingestion/presentation/test_config.py:18-144` — 9 tests: defaults, env override, validation |

**Observability-related settings:**
| Setting | Default | Env Var | Purpose |
|---------|---------|---------|---------|
| `LOG_LEVEL` | `"INFO"` | `AI_SHORTS_LOG_LEVEL` | Python logging level |
| `LOG_FORMAT` | `"json"` | `AI_SHORTS_LOG_FORMAT` | `"json"` or `"text"` |
| `ENVIRONMENT` | `"development"` | `AI_SHORTS_ENVIRONMENT` | `development\|testing\|production` |
| `SECRET_KEY` | `"change-me-in-production"` | `AI_SHORTS_SECRET_KEY` | App secret |

---

## 8. Test Coverage Summary

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| middleware.py | test_middleware.py | 12 | RequestID (3), CorrelationID (3), Timing (3), Recovery (3) |
| logging_config.py | test_logging.py | 10 | setup_logging (5), JSONFormatter (3), RequestContextFilter (2) |
| health.py | test_health.py | 3 | Liveness (1), Readiness (2) |
| exceptions.py | test_exceptions.py | 10 | Error mapper (6), Exception handlers (4) |
| app.py | test_app.py | 10 | Factory (8), Middleware (2) |
| config.py | test_config.py | 9 | Defaults (2), Env (4), Validation (3) |

**Total observability-related tests**: 54

---

## 9. Gaps & Recommendations

### Identified Gaps

1. **No access log middleware**: The design doc (`observability.md`) specified an `AccessLogMiddleware` using structlog that logs `method`, `path`, `status`, `duration_ms`, `request_id`, `correlation_id`, `user_agent`. This was NOT implemented. Instead, request context is available via `request.state` but no middleware logs every request.

2. **No `duration_ms` in log records**: The timing middleware stores `duration_ms` on `request.state` but it is not injected into log records by `RequestContextFilter`.

3. **No structlog**: The design doc specified `structlog` but the implementation uses stdlib `logging` with a custom `JSONFormatter`. This is a deliberate simplification.

4. **Stacktrace for 5xx only**: All exception handlers use `exc_info=True`, which means stacktraces are logged for ALL handled exceptions (including 404, 409, 422). The production-readiness checklist specifies "stacktrace logged for 5xx errors only" — this is NOT enforced at the handler level. However, in practice, domain validation errors (404, 409, 422) are handled by the router's `_error_response()` helper which calls `problem_response()` directly without logging, so stacktraces are only logged for the exception handlers (PersistenceError, InfrastructureError, FoundationError, generic Exception).

5. **No metrics endpoint**: The design doc mentioned future Prometheus metrics. Not implemented (marked as future).

6. **No log rotation or shipping**: Single StreamHandler to stdout. No file handler, no log shipping, no structured log aggregation.

7. **SECRET_KEY default is insecure**: Default value `"change-me-in-production"` is a placeholder. No startup validation that it was changed in production.

### Recommendations

1. **Add AccessLogMiddleware**: Log every request with method, path, status, duration, request_id, correlation_id. This is essential for production observability.

2. **Inject duration_ms into log records**: Extend `RequestContextFilter` to read `request.state.duration_ms` and add it to log records.

3. **Conditional stacktrace logging**: Only log `exc_info=True` for 5xx errors. For 4xx, log the error code and message without the stacktrace.

4. **Validate SECRET_KEY in production**: Add a startup check that `SECRET_KEY != "change-me-in-production"` when `ENVIRONMENT == "production"`.

5. **Add file logging with rotation**: For production deployments, add a `RotatingFileHandler` or use a log aggregator.
