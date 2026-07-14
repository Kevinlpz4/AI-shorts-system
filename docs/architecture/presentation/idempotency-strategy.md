# Design: Idempotency Strategy

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D10 (Idempotency Strategy)

---

## 1. Problem

HTTP POST requests are not idempotent by default. If a client sends a POST and the connection drops before receiving a response, the client doesn't know if the operation succeeded. Retrying could create duplicate resources.

## 2. Strategy

### Current Phase (Epic 6): Header-Based Idempotency

Clients include `Idempotency-Key` header on POST requests. The server:
1. Checks if the key has been seen recently
2. If yes → returns the cached response (200/201/409)
3. If no → processes the request, stores the key + response, returns result

### Future Phase: Idempotency Key Storage

Store idempotency keys in a dedicated table with TTL (time-to-live) for automatic cleanup.

## 3. Implementation Design

### Header

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

- UUID v4 recommended
- Required for POST endpoints (recommended, not mandatory)
- Not needed for GET, PUT, PATCH (GET is safe, PUT/PATCH are idempotent by HTTP spec)
- DELETE is idempotent by HTTP spec

### Flow

```
Client sends POST with Idempotency-Key
    │
    ▼
Middleware/Handler checks key in store
    │
    ├── Key exists → Return cached response
    │
    └── Key doesn't exist → Process request
            │
            ├── Success → Store key + response, return 201
            │
            └── Failure → Store key + error response, return error
```

### Storage (Current)

In-memory dictionary with TTL (per-process, not distributed):

```python
# presentation/idempotency/store.py
import time
from dataclasses import dataclass

@dataclass
class IdempotencyEntry:
    status_code: int
    response_body: dict
    created_at: float

class InMemoryIdempotencyStore:
    """In-process idempotency store. NOT distributed."""

    def __init__(self, ttl_seconds: int = 86400):  # 24h default
        self._store: dict[str, IdempotencyEntry] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> IdempotencyEntry | None:
        entry = self._store.get(key)
        if entry and (time.time() - entry.created_at) < self._ttl:
            return entry
        if entry:
            del self._store[key]  # Expired
        return None

    def set(self, key: str, status_code: int, response_body: dict):
        self._store[key] = IdempotencyEntry(
            status_code=status_code,
            response_body=response_body,
            created_at=time.time(),
        )
```

### Middleware Integration

```python
# presentation/middleware/idempotency.py
from starlette.middleware.base import BaseHTTPMiddleware

class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, store: InMemoryIdempotencyStore):
        super().__init__(app)
        self._store = store

    async def dispatch(self, request, call_next):
        if request.method != "POST":
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        # Check cache
        cached = self._store.get(key)
        if cached:
            return JSONResponse(
                status_code=cached.status_code,
                content=cached.response_body,
                headers={"Idempotency-Key": key, "X-Idempotent-Replay": "true"},
            )

        # Process request
        response = await call_next(request)

        # Store successful responses
        if response.status_code in (200, 201):
            body = await self._read_response_body(response)
            self._store.set(key, response.status_code, body)
            return JSONResponse(
                status_code=response.status_code,
                content=body,
                headers={"Idempotency-Key": key},
            )

        return response
```

## 4. 409 Conflict Response

When a duplicate request is detected (same key, different payload):

```json
{
  "type": "about:blank",
  "title": "Idempotency Conflict",
  "status": 409,
  "detail": "Request with this Idempotency-Key was already processed with a different payload",
  "instance": "/api/v1/sources",
  "error_code": "IDEMPOTENCY_CONFLICT"
}
```

## 5. Client Retry Pattern

```python
import httpx
import uuid

def create_source_with_retry(data: dict, max_retries: int = 3):
    key = str(uuid.uuid4())
    for attempt in range(max_retries):
        try:
            response = httpx.post(
                "http://localhost:8000/api/v1/sources",
                json=data,
                headers={"Idempotency-Key": key},
                timeout=10.0,
            )
            if response.status_code in (200, 201, 409):
                return response  # 409 = already processed, safe to ignore
        except httpx.TimeoutException:
            continue  # Retry with same key
    raise Exception("Max retries exceeded")
```

## 6. Timeout Handling

- Idempotency keys expire after 24 hours (configurable)
- Expired keys are cleaned up on access (lazy cleanup)
- Future: periodic cleanup job for memory efficiency

## 7. Limitations (Current)

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| In-memory only | Lost on restart | Acceptable for single-instance deployment |
| Not distributed | Different instances have different stores | Future: Redis-backed store |
| No payload validation | Same key + different payload returns cached | Add payload hash comparison (future) |

## 8. Future Evolution

1. **Redis-backed store**: Distributed idempotency across instances
2. **Payload hash validation**: Detect conflicting payloads with same key
3. **Configurable TTL**: Per-endpoint TTL configuration
4. **Async cleanup**: Background job to purge expired keys

---

*See also: `api-design.md`, `exception-handling.md`, `observability.md`*
