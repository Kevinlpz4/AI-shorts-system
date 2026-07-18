# Learning BC — Observability Assessment

> **Date**: 2026-07-18
> **BC**: Learning Intelligence
> **Version**: 1.0 (Sprint 7.8)
> **Current Observability Score**: 3/10

---

## 1. Current State

### 1.1 What We HAVE

| Capability | Implementation | File | Status |
|------------|---------------|------|--------|
| Request ID propagation | `RequestIdMiddleware` — generates UUID4, sets `X-Request-ID` + `X-Correlation-ID` | `presentation/middleware/request_id.py` | ✅ |
| Response timing | `TimingMiddleware` — adds `X-Response-Time` header in ms | `presentation/middleware/timing.py` | ✅ |
| RFC 9457 Problem Details | Structured error responses with type, title, status, detail, instance | `presentation/schemas/problem_details.py` | ✅ |
| OpenAPI documentation | Custom schema with metadata, tags, contact info | `presentation/openapi/customization.py` | ✅ |
| Health probes | 3 endpoints: /health, /ready, /live | Presentation layer | ✅ |

### 1.2 What We're MISSING

| Category | Status | Impact |
|----------|--------|--------|
| Structured logging (JSON) | ❌ None | Can't query logs, can't aggregate errors |
| Distributed tracing | ❌ None | Can't trace requests across components |
| Metrics collection | ❌ None | Can't measure throughput, latency, errors |
| Request body logging | ❌ None | Can't debug malformed requests |
| Error rate tracking | ❌ None | Don't know failure patterns |
| Dependency health checks | ❌ None | Health endpoints return "healthy" even when DB is down |
| Log correlation | ❌ None | Can't link logs to specific requests |
| Audit trail | ❌ None | Domain events exist but no persistent audit log |

**Current score: 3/10** — We have basic request tracking but no operational visibility.

---

## 2. Detailed Gap Analysis

### 2.1 Structured Logging

**Current**: No logging at all. No `logging` configuration, no JSON output, no log levels.

**Impact**: When something fails in production, there's NOTHING to look at. No logs = blind.

**Required**:
- JSON-formatted log entries for machine parsing
- Request-scoped context (request_id, correlation_id, endpoint, duration)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Sensitive data masking (no API keys, no PII in logs)
- Log rotation and retention policies

### 2.2 Distributed Tracing

**Current**: No trace context propagation. Request ID exists but isn't tied to any tracing system.

**Impact**: Can't see the full journey of a request through Domain, Application, Infrastructure, and Persistence layers.

**Required**:
- OpenTelemetry SDK integration
- Trace context propagation through all layers
- Span creation for each service call
- Export to Jaeger/Zipkin/OTLP collector
- Context propagation across async boundaries

### 2.3 Metrics Collection

**Current**: Zero metrics. No counters, gauges, or histograms.

**Impact**: Can't answer: "How many predictions per minute?" "What's the p95 latency?" "What's the error rate?"

**Required** (see `learning-metrics-catalog.md` for full catalog):
- Counters: requests, predictions, feedback, errors
- Gauges: active signals, datasets, artifacts
- Histograms: latency for all operations
- Export via `/metrics` endpoint for Prometheus scraping

### 2.4 Health Checks

**Current**: Three health endpoints that always return "healthy" regardless of actual state.

```json
// GET /health always returns:
{"status": "healthy", "service": "learning-intelligence-api"}
```

**Impact**: Load balancers think the service is healthy when the database is unreachable.

**Required**:
- `/health` → deep check: DB connectivity, cache availability, disk space
- `/ready` → readiness check: can accept traffic (dependencies available)
- `/live` → liveness check: process is alive (can be lightweight)
- Each check should verify actual dependencies, not just return static JSON

### 2.5 Request/Response Logging

**Current**: No request or response body logging.

**Impact**: When a 400 error occurs, can't see what the client actually sent.

**Required**:
- Log request method, path, headers, body (with PII masking)
- Log response status, body (with sensitive data filtering)
- Configurable log levels per endpoint (health endpoints should be DEBUG)
- Maximum body size for logging (prevent memory issues with large payloads)

### 2.6 Error Rate Tracking

**Current**: Errors return RFC 9457 Problem Details but are not counted or tracked.

**Impact**: No way to know if error rate spiked at 3 AM.

**Required**:
- Counter for errors by endpoint, status code, error type
- Alerting threshold configuration
- Error rate dashboard panel
- Correlation with request_id for debugging

---

## 3. Recommendations

### 3.1 Add `structlog` for Structured JSON Logging

**Why structlog over standard logging?**
- Native JSON serialization
- Context binding (bind request_id, user_id, etc.)
- Processor pipeline for adding timestamps, log levels
- Thread-safe context variables
- Excellent FastAPI integration

**Implementation**:
```python
# infrastructure/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
```

**Where to instrument**:
- Every router endpoint: log request start/end
- Every service method: log business operations
- Every repository call: log persistence operations
- Every event handler: log event processing
- Every error: log with full context

### 3.2 Add OpenTelemetry for Distributed Tracing

**Why OpenTelemetry?**
- Vendor-neutral (works with Jaeger, Zipkin, Grafana Tempo)
- Auto-instrumentation for FastAPI, SQLAlchemy, HTTP clients
- Correlates traces with logs and metrics
- Industry standard

**Implementation**:
```python
# infrastructure/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

**Span hierarchy**:
```
[HTTP Request]
  └── [Router: POST /predict]
       └── [Service: PredictionService.predict]
            └── [Repository: FeedbackRecordRepo.find_by_article]
                 └── [SQL: SELECT ...]
```

### 3.3 Add `prometheus_client` for Metrics

**Why prometheus_client?**
- Lightweight, battle-tested
- FastAPI integration via `prometheus_fastapi_instrumentator`
- Standard metrics format
- Works with Grafana dashboards

**Implementation**:
```python
# infrastructure/metrics.py
from prometheus_client import Counter, Gauge, Histogram

# Defined in learning-metrics-catalog.md
learning_predictions_total = Counter(
    'learning_predictions_total',
    'Total predictions made',
    ['source', 'result']
)

learning_prediction_latency_ms = Histogram(
    'learning_prediction_latency_ms',
    'Prediction endpoint latency',
    buckets=[10, 25, 50, 100, 200, 500, 1000]
)
```

**Endpoint**: `/metrics` — exposed for Prometheus scraping

### 3.4 Add Request/Response Logging Middleware

```python
# presentation/middleware/logging.py
class RequestLoggingMiddleware:
    async def __call__(self, request, call_next):
        # Log request
        logger.info("request_started",
            method=request.method,
            path=request.url.path,
            request_id=get_request_id(),
        )
        response = await call_next(request)
        # Log response
        logger.info("request_completed",
            status=response.status_code,
            duration_ms=elapsed,
            request_id=get_request_id(),
        )
        return response
```

### 3.5 Wire Health Checks to Dependencies

```python
# presentation/routers/health.py
async def health_check():
    checks = {}
    checks["database"] = await check_db_connection()
    checks["cache"] = await check_cache_availability()
    overall = "healthy" if all(checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
```

---

## 4. Observability Architecture Design

### 4.1 Target Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Request   │  │ Timing   │  │ Request Logging  │  │
│  │ ID MW     │  │ MW       │  │ Middleware       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│       │              │              │                │
│       ▼              ▼              ▼                │
│  ┌──────────────────────────────────────────────┐   │
│  │            structlog Context Binding          │   │
│  │  (request_id, correlation_id, endpoint)      │   │
│  └──────────────────────────────────────────────┘   │
│       │                                              │
│       ▼                                              │
│  ┌──────────────────────────────────────────────┐   │
│  │           OpenTelemetry Span Creation         │   │
│  │  (auto-instrument FastAPI + SQLAlchemy)       │   │
│  └──────────────────────────────────────────────┘   │
│       │                                              │
│       ▼                                              │
│  ┌──────────────────────────────────────────────┐   │
│  │         Prometheus Metrics Emission           │   │
│  │  (counters, gauges, histograms)              │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
  ┌─────────┐  ┌──────────┐  ┌───────────┐
  │ Jaeger  │  │ Grafana  │  │ Prometheus│
  │ (traces)│  │(dashbrd) │  │ (metrics) │
  └─────────┘  └──────────┘  └───────────┘
```

### 4.2 Request Lifecycle with Observability

```
1. Client sends request
   → RequestIdMiddleware: generate X-Request-ID, bind to structlog context
   → TimingMiddleware: record start time

2. Router receives request
   → OpenTelemetry: create HTTP span
   → structlog: log request_started (method, path, request_id)

3. Application layer processes
   → OpenTelemetry: create service span (child of HTTP span)
   → structlog: log service operation
   → Prometheus: increment request counter

4. Infrastructure layer executes
   → OpenTelemetry: create infrastructure span
   → structlog: log persistence operation

5. Response returned
   → OpenTelemetry: close all spans
   → TimingMiddleware: record X-Response-Time
   → structlog: log request_completed (status, duration)
   → Prometheus: observe latency histogram

6. Background
   → OpenTelemetry: BatchSpanProcessor exports to Jaeger
   → Prometheus: /metrics endpoint exposed
   → structlog: JSON logs available for aggregation
```

### 4.3 Dashboard Panels (Preview)

See `learning-dashboard-design.md` for full dashboard layout.

### 4.4 Alerting (Preview)

See `learning-alerting-guide.md` for full alerting rules.

---

## 5. Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | structlog (structured logging) | 1-2 days | Can finally see what's happening |
| P0 | Request/response logging middleware | 0.5 day | Debug production issues |
| P0 | prometheus_client (metrics) | 1-2 days | Measure throughput, latency, errors |
| P1 | Health check dependency wiring | 0.5 day | Know when deps are down |
| P1 | OpenTelemetry (tracing) | 2-3 days | Full request journey visibility |
| P2 | Log aggregation setup | 1 day | Centralized log search |
| P2 | Dashboard creation | 1 day | Visual monitoring |
| P3 | Alerting rules | 0.5 day | Proactive issue detection |

**Total estimated effort: 7-10 days**

---

## 6. Summary

The Learning BC has the FOUNDATIONS for observability (request IDs, timing, problem details) but lacks the ACTUAL observability stack (logging, tracing, metrics). This is a common pattern — the plumbing is there, but the instrumentation is missing.

The fix is straightforward and well-understood. No architectural changes needed — just adding standard Python observability libraries and wiring them into existing middleware.

**Current Score**: 3/10
**Target Score**: 9/10 (after P0+P1 implementation)

---

*Generated: 2026-07-18 | Sprint 7.8 | Learning BC v1.0*
