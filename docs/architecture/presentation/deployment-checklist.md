# Deployment Checklist — Ingestion API

**Sprint**: 6.5 — API Hardening & Production Readiness
**Date**: 2026-07-15
**Status**: COMPLETE

---

## Pre-Deployment

### Environment Variables (Required)

| Variable | Example | Notes |
|----------|---------|-------|
| `AI_SHORTS_SECRET_KEY` | *(64-char random string)* | **REQUIRED in production** — startup fails without it |
| `AI_SHORTS_ENVIRONMENT` | `production` | Must be `production` |
| `AI_SHORTS_DATABASE_URL` | `postgresql://user:pass@host/db` | PostgreSQL for production |
| `AI_SHORTS_CORS_ORIGINS` | `["https://app.example.com"]` | No wildcards |
| `AI_SHORTS_ALLOWED_HOSTS` | `["api.example.com", "*.example.com"]` | Trusted hosts |

### Environment Variables (Optional)

| Variable | Default | Notes |
|----------|---------|-------|
| `AI_SHORTS_HOST` | `0.0.0.0` | Bind address |
| `AI_SHORTS_PORT` | `8000` | Server port |
| `AI_SHORTS_LOG_LEVEL` | `INFO` | `DEBUG` in production exposes sensitive info |
| `AI_SHORTS_LOG_FORMAT` | `json` | `json` for production |
| `AI_SHORTS_DEBUG` | `false` | Must be `false` in production |
| `AI_SHORTS_SECURITY_HEADERS_ENABLED` | `true` | Disable only for internal APIs |

### Generate Secret Key

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

---

## Startup Validation

The application validates configuration at startup:

1. **SECRET_KEY**: Must be ≥ 8 characters. In production, must not be `change-me-in-production`.
2. **ENVIRONMENT**: Must be `development`, `testing`, or `production`.
3. **CORS_ORIGINS**: Must not contain `*` wildcard.
4. **LOG_FORMAT**: Must be `json` or `text`.

**Invalid configuration raises `RuntimeError` or `ValidationError` at startup.**

---

## Health Checks

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `GET /health/live` | Liveness probe | `200 {"status": "alive"}` |
| `GET /health/ready` | Readiness probe (DB check) | `200 {"status": "ready"}` or `503 {"status": "not_ready"}` |

### Kubernetes Example

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Middleware Order

The middleware stack executes in this order (outermost first):

1. **CORSMiddleware** — CORS headers
2. **SecurityHeadersMiddleware** — HSTS, X-Frame-Options, etc.
3. **TrustedHostMiddleware** — Host header validation
4. **RecoveryMiddleware** — Catch-all exception handler
5. **TimingMiddleware** — Request duration tracking
6. **RequestIDMiddleware** — X-Request-ID propagation
7. **CorrelationIDMiddleware** — X-Correlation-ID propagation

---

## Security Headers

All responses include:

```
Strict-Transport-Security: max-age=15768000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## CORS Configuration

```bash
# Production example
AI_SHORTS_CORS_ORIGINS='["https://app.example.com","https://admin.example.com"]'
```

**Rules:**
- No `*` wildcard (rejected by validator)
- Specific origins only
- Empty list disables CORS

---

## Trusted Hosts

```bash
# Production example
AI_SHORTS_ALLOWED_HOSTS='["api.example.com","*.example.com"]'
```

**Rules:**
- Default: `["localhost", "127.0.0.1"]` (development only)
- Use `["*"]` to allow all (testing only)
- Supports wildcard subdomains: `*.example.com`

---

## Database

| Environment | Database | Notes |
|-------------|----------|-------|
| development | SQLite | File-based, auto-created |
| testing | SQLite InMemory | Fresh per test |
| production | PostgreSQL | Required for async, connection pooling |

---

## Logging

| Setting | Development | Production |
|---------|-------------|------------|
| `LOG_LEVEL` | `DEBUG` | `INFO` |
| `LOG_FORMAT` | `text` | `json` |

JSON log fields:
```json
{
  "timestamp": "2026-07-15T00:00:00,000",
  "level": "INFO",
  "message": "Request processed",
  "logger": "ingestion.presentation.middleware",
  "request_id": "abc-123",
  "correlation_id": "abc-123"
}
```

---

## Post-Deployment Verification

1. `GET /health/live` → `200 {"status": "alive"}`
2. `GET /health/ready` → `200 {"status": "ready"}`
3. `GET /openapi.json` → Valid OpenAPI 3.1 schema
4. Verify security headers in response:
   ```bash
   curl -I http://localhost:8000/health/live
   ```
5. Verify CORS:
   ```bash
   curl -H "Origin: https://app.example.com" -I http://localhost:8000/health/live
   ```
6. Verify TrustedHost rejection:
   ```bash
   curl -H "Host: evil.com" http://localhost:8000/health/live
   # Should return 400
   ```
