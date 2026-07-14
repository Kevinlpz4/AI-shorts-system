# API Hardening Report — Ingestion API

**Sprint**: 6.5 — API Hardening & Production Readiness
**Date**: 2026-07-15
**Status**: COMPLETE

---

## Executive Summary

Sprint 6.5 elevated Production Readiness from **92.5% (37/40)** to **100% (40/40)**. All 3 FAIL items from Sprint 6.4 have been resolved. New middleware (SecurityHeaders, TrustedHost) added. Configuration hardened with validators and startup checks. 39 new tests, 242 total presentation tests, zero regressions.

---

## Before vs After

| Metric | Sprint 6.4 | Sprint 6.5 | Change |
|--------|-----------|-----------|--------|
| Production Readiness | 37/40 (92.5%) | 40/40 (100%) | +3 |
| Middleware | 4 | 6 | +2 |
| Config Validators | 1 (ENVIRONMENT) | 4 (SECRET_KEY, CORS, LOG_FORMAT, ENVIRONMENT) | +3 |
| Security Headers | 0 | 6 | +6 |
| Trusted Host Validation | No | Yes | ✅ |
| SECRET_KEY Startup Validation | No | Yes (production) | ✅ |
| Presentation Tests | 203 | 242 | +39 |
| FAIL Items | 3 | 0 | -3 |

---

## What Was Implemented

### 1. SecurityHeadersMiddleware

Adds 6 security headers to every response:
- `Strict-Transport-Security: max-age=15768000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

Configurable via `AI_SHORTS_SECURITY_HEADERS_ENABLED` (default: `true`).

### 2. TrustedHostMiddleware

Validates `Host` header against allowed hosts list. Returns 400 Problem Details for invalid hosts.

- Default: `["localhost", "127.0.0.1"]`
- Supports wildcard subdomains: `*.example.com`
- Configurable via `AI_SHORTS_ALLOWED_HOSTS`

### 3. SECRET_KEY Validation

Two layers:
1. **Pydantic validator**: Rejects keys < 8 characters at Settings construction time
2. **Startup check**: `_validate_startup_settings()` raises `RuntimeError` in production if SECRET_KEY is insecure

### 4. Configuration Validators

| Validator | Rejects |
|-----------|---------|
| `SECRET_KEY` | Keys < 8 characters |
| `CORS_ORIGINS` | Wildcard `*` |
| `LOG_FORMAT` | Values other than `json` or `text` |
| `ENVIRONMENT` | Values other than `development`, `testing`, `production` |

### 5. Startup Validation

`_validate_startup_settings()` runs at `create_app()` time:
- Production + insecure SECRET_KEY → `RuntimeError`
- Production + DEBUG=True → warning log
- Production + localhost CORS → warning log

### 6. Middleware Order Fix

Corrected middleware execution order:
```
CORS → SecurityHeaders → TrustedHost → Recovery → Timing → RequestID → CorrelationID → Handler
```

RequestID is outermost among custom middleware because CorrelationIDMiddleware reads `request.state.request_id` as fallback.

### 7. Bug Fix

Fixed `CorrelationIDMiddleware` crash when `request_id` is None (e.g., for 404 responses before RequestIDMiddleware runs). Added fallback to `"-"`.

---

## Tests Added

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestSecurityHeaders | 6 | All 6 headers present on OK, error, and health responses |
| TestSecurityHeadersDisabled | 1 | Headers not added when disabled |
| TestTrustedHostMiddleware | 5 | Allowed, rejected, wildcard, subdomain, Problem Details |
| TestSecretKeyValidation | 4 | Short, empty, valid, preserved |
| TestProductionSecretKeyValidation | 3 | Production reject, production accept, testing accept |
| TestCORSValidation | 3 | Wildcard reject, specific accept, empty accept |
| TestLogFormatValidation | 3 | Invalid reject, json accept, text accept |
| TestEnvironmentValidation | 3 | Invalid reject, all 3 valid values |
| TestStartupValidation | 3 | Debug warning, CORS warning, dev no warnings |
| TestErrorSurfaceAudit | 4 | No stacktrace, Problem Details, 404, no internal details |
| TestMiddlewareRegistration | 2 | All 6 registered, correct order |
| **TOTAL** | **39** | |

---

## OpenAPI Production Review

| Check | Status | Evidence |
|-------|--------|----------|
| Title includes version | ✅ | `AI Shorts System — Ingestion API v1.0.0` |
| Version matches settings | ✅ | `openapi_version: str = "1.0.0"` |
| Tags for all routers | ✅ | Sources, Feeds, Articles, Categories, Topics, System |
| operationId for all operations | ✅ | FastAPI auto-generates from function names |
| No orphan endpoints | ✅ | Verified via test |
| Schemas section populated | ✅ | Request/response models present |
| Problem Details in error schemas | ✅ | RFC 9457 format |

**Deferred to Sprint 6.6:**
- `contact` and `license` in OpenAPI info
- `servers` section with production URL
- `security` schemes (requires auth layer)
- Request/response examples

---

## Error Surface Audit

| Check | Status | Evidence |
|-------|--------|----------|
| No stack traces in 4xx responses | ✅ | Router helpers call `problem_response()` directly |
| No stack traces in 500 responses | ✅ | RecoveryMiddleware returns generic message |
| No internal messages to client | ✅ | "An unexpected error occurred." |
| Logs contain full details | ✅ | `logger.exception()` with exc_info=True |
| Problem Details consistent | ✅ | All errors use RFC 9457 format |
| Content-Type correct | ✅ | `application/problem+json` on all errors |

---

## Rate Limiting Decision

**Status**: DEFERRED (YAGNI)

See [rate-limiting-adr.md](rate-limiting-adr.md) for full rationale.

**Summary**: Internal API, no multi-tenancy, no external clients. Rate limiting should be added at infrastructure level (API gateway) when needed, not in application code.

---

## Files Changed

| File | Change |
|------|--------|
| `src/ingestion/presentation/middleware.py` | +SecurityHeadersMiddleware, +TrustedHostMiddleware, docstring update |
| `src/ingestion/presentation/config.py` | +ALLOWED_HOSTS, +SECURITY_HEADERS_ENABLED, +3 validators |
| `src/ingestion/presentation/app.py` | +_validate_startup_settings, +new middleware wiring, middleware order fix |
| `tests/ingestion/presentation/conftest.py` | +ALLOWED_HOSTS to test settings |
| `tests/ingestion/presentation/test_hardening.py` | NEW — 39 tests |
| `tests/ingestion/presentation/test_app.py` | Updated middleware order assertion |
| `tests/ingestion/presentation/test_*.py` | +ALLOWED_HOSTS=["*"] to all _make_settings() |

---

## Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| No auth layer | Medium | Deferred to future sprint; API is internal |
| No rate limiting | Low | Deferred per YAGNI; use API gateway |
| HSTS requires HTTPS | Medium | Ensure HTTPS termination at load balancer |
| CSP is very restrictive | Low | API-only; no frontend assets served |
