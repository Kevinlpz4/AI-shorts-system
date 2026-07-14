# Design: Observability

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D7 (Health Endpoints), D8 (Observability from Day One)

---

## 1. Observability Stack

```
Request → [RequestID] → [CorrelationID] → [Timing] → [AccessLog] → Handler
                                                │
                                                ▼
                                         Structured Log (JSON)
                                         ├── request_id
                                         ├── correlation_id
                                         ├── method, path, status
                                         ├── duration_ms
                                         ├── user_agent
                                         └── timestamp
```

## 2. Middleware Implementations

### Request ID Middleware

```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
```

### Correlation ID Middleware

```python
# middleware/correlation_id.py
CORRELATION_ID_HEADER = "X-Correlation-ID"

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, request.state.request_id)
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
```

### Timing Middleware

```python
# middleware/timing.py
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        request.state.duration_ms = duration_ms
        return response
```

### Access Log Middleware

```python
# middleware/access_log.py
import structlog

logger = structlog.get_logger("access")

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=getattr(request.state, "duration_ms", None),
            request_id=getattr(request.state, "request_id", None),
            correlation_id=getattr(request.state, "correlation_id", None),
            user_agent=request.headers.get("user-agent"),
        )
        return response
```

## 3. Structured Logging

Use `structlog` for JSON-structured logs:

```python
# config/logging.py
import structlog

def configure_logging(log_level: str, log_format: str):
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

## 4. Health Check Implementation

### GET /health — Full Health Check

```python
@router.get("/health")
async def health_check(session_factory=Depends(get_session_factory)):
    checks = {}

    # Database check
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "detail": str(e)}

    overall = "healthy" if all(c["status"] == "healthy" for c in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }
```

### GET /health/live — Liveness Probe

```python
@router.get("/health/live")
async def liveness():
    return {"status": "alive"}
```

### GET /health/ready — Readiness Probe

```python
@router.get("/health/ready")
async def readiness(session_factory=Depends(get_session_factory)):
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")
```

## 5. Exception Logging

```python
# exceptions/handlers.py
import structlog

logger = structlog.get_logger("exception")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=request.url.path,
        method=request.method,
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(
        status_code=500,
        content={"type": "about:blank", "title": "Internal Server Error", "status": 500},
    )
```

## 6. Metrics (Future — Design Only)

When Prometheus metrics are needed:

```python
# future: middleware/metrics.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("http_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "path"])
```

## 7. Request Context Propagation

```python
# All middleware stores context on request.state:
# request.state.request_id
# request.state.correlation_id
# request.state.duration_ms

# Structlog contextvars propagation:
structlog.contextvars.clear_contextvars()
structlog.contextvars.bind_contextvars(
    request_id=request.state.request_id,
    correlation_id=request.state.correlation_id,
)
```

---

*See also: `presentation-design.md`, `composition-root.md`*
