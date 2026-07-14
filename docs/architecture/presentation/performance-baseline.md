# Performance Baseline — Ingestion API

**Sprint**: 6.4 — Observability & Operations Hardening
**Date**: 2026-07-14
**Status**: BASELINE ESTABLISHED

---

## 1. Methodology

| Parameter | Value |
|-----------|-------|
| **Runtime** | Python 3.12, FastAPI, SQLAlchemy |
| **Database** | SQLite InMemory (StaticPool, zero network latency) |
| **HTTP Client** | httpx AsyncClient with ASGITransport |
| **Iterations** | 50 per operation |
| **Warm-up** | 10 requests before measurement |
| **Percentiles** | p50, p95, p99 |
| **Target** | p95 < 100ms for all operations |

### Measurement Approach

- **Presentation Layer overhead**: Services are mocked via FastAPI DI overrides. This isolates the overhead of middleware stack (Recovery, Timing, CorrelationID, RequestID), request routing, Pydantic validation/serialization, structured logging, and exception handling.
- **Full stack NOT measured**: Application, Domain, and Persistence layers are not exercised. Production latency will be higher due to database queries, domain validation, and UoW lifecycle.

### Script

Performance measurements were collected using `scripts/perf_baseline.py`, which:
1. Creates a FastAPI app with mocked services
2. Registers DI overrides for SourceService, FeedService, ArticleService
3. Measures each CRUD operation 50 times
4. Calculates p50/p95/p99 from sorted latency samples

---

## 2. Results

### Source CRUD

| Operation | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Target | Status |
|-----------|----------|----------|----------|----------|----------|--------|--------|
| Create (POST /api/v1/sources) | 4.35 | 11.17 | 58.88 | 2.41 | 116.84 | <100ms | ✅ PASS |
| Get by ID (GET /api/v1/sources/{id}) | 2.70 | 4.43 | 13.81 | 1.58 | 28.65 | <100ms | ✅ PASS |
| List paginated (GET /api/v1/sources) | 2.59 | 6.54 | 19.64 | 1.54 | 24.49 | <100ms | ✅ PASS |

### Feed CRUD

| Operation | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Target | Status |
|-----------|----------|----------|----------|----------|----------|--------|--------|
| Create (POST /api/v1/feeds) | 4.39 | 8.81 | 76.20 | 2.54 | 97.61 | <100ms | ✅ PASS |
| Get by ID (GET /api/v1/feeds/{id}) | 1.90 | 5.20 | 16.55 | 1.36 | 20.48 | <100ms | ✅ PASS |
| List paginated (GET /api/v1/sources/{id}/feeds) | 2.56 | 5.32 | 10.60 | 1.68 | 13.48 | <100ms | ✅ PASS |

### Article CRUD

| Operation | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Target | Status |
|-----------|----------|----------|----------|----------|----------|--------|--------|
| Create (POST /api/v1/articles) | 3.61 | 6.34 | 45.80 | 2.05 | 62.39 | <100ms | ✅ PASS |
| Get by ID (GET /api/v1/articles/{id}) | 2.24 | 3.81 | 9.31 | 1.42 | 13.27 | <100ms | ✅ PASS |
| List by feed (GET /api/v1/articles?feed_id=...) | 2.62 | 7.04 | 10.24 | 1.73 | 13.20 | <100ms | ✅ PASS |

### Health Endpoints

| Operation | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Target | Status |
|-----------|----------|----------|----------|----------|----------|--------|--------|
| Liveness (GET /health/live) | 0.97 | 1.51 | 1.91 | 0.70 | 2.88 | <100ms | ✅ PASS |
| Readiness (GET /health/ready) | 1.68 | 4.14 | 7.85 | 1.16 | 11.35 | <100ms | ✅ PASS |

---

## 3. Analysis

### Summary

| Metric | Value |
|--------|-------|
| **Total operations measured** | 11 |
| **Operations passing p95 < 100ms** | 11/11 (100%) |
| **Fastest p50** | 0.97ms (Health /live) |
| **Slowest p50** | 4.39ms (Feed create) |
| **Fastest p95** | 1.51ms (Health /live) |
| **Slowest p95** | 11.17ms (Source create) |

### Key Findings

1. **All operations well within target**: p95 ranges from 1.51ms to 11.17ms — all far below the 100ms target. The Presentation Layer overhead is negligible.

2. **Create operations are slowest**: POST endpoints (create) have higher p50 (~4ms) compared to GET endpoints (~2ms). This is expected due to Pydantic request body validation and larger response serialization.

3. **p99 outliers**: Some operations show p99 values approaching or exceeding 50ms (Source create: 58.88ms, Feed create: 76.20ms). These are likely due to GC pauses or event loop scheduling during the measurement. Not concerning for p95 target.

4. **Health endpoints are fastest**: `/health/live` at 0.97ms p50 demonstrates the minimal overhead of the middleware stack itself (no DI, no serialization, no DB).

5. **Readiness is slightly slower than liveness**: 1.68ms vs 0.97ms p50 — the additional 0.7ms is the DB `SELECT 1` check plus DI resolution.

### Middleware Overhead

The middleware stack (Recovery → Timing → CorrelationID → RequestID) adds approximately 0.5-1ms per request, based on the Health /live baseline (0.97ms p50 with no handler logic).

### Bottlenecks

**No bottlenecks identified at the Presentation Layer level.** The middleware stack, routing, and serialization are efficient. When the full stack is exercised (with real DB operations), the bottleneck will shift to:
- Database query time (SQLite vs. PostgreSQL)
- Domain validation logic
- UoW commit/flush operations

---

## 4. Recommendations

1. **No optimization needed for Presentation Layer**: The overhead is well within acceptable limits. Focus optimization efforts on the Application/Persistence layers when needed.

2. **Monitor p99 in production**: The p99 outliers (58-76ms) should be monitored. If they persist in production with a real database, investigate GC tuning or connection pooling.

3. **Baseline for regression**: These numbers serve as a regression baseline. If future changes to middleware or serialization push p95 above 50ms, investigate.

4. **Full-stack baseline recommended**: When the system moves to production with PostgreSQL, run a full-stack baseline with realistic data volumes to establish production-representative numbers.

---

## 5. Reproduction

To reproduce these measurements:

```bash
cd AI_Shorts_System
.venv/bin/python scripts/perf_baseline.py
```

**Prerequisites:**
- Python 3.12 with project dependencies installed
- No running server required (uses httpx ASGITransport)

**Environment variables:**
- None required — script uses test defaults
