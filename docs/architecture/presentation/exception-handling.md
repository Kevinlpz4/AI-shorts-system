# Design: Exception Handling & Error Mapping

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D3 (RFC 9457 Problem Details)

---

## 1. Error Flow

```
Application Layer                        Presentation Layer
─────────────────                        ──────────────────

Result.failure(Error)                    RFC 9457 Problem Details JSON
    │                                         ▲
    ▼                                         │
ApplicationErrorCode                    ErrorToProblemDetails mapper
    │                                         ▲
    ▼                                         │
IngestionErrorCode (domain)             HTTP Status Code determination
    │
    ▼
FoundationError hierarchy
```

The Application Layer returns `Result[T]` with `Error(code, message)`. The Presentation Layer maps these to RFC 9457 Problem Details JSON responses.

## 2. Error Hierarchy → HTTP Status Mapping

```
FoundationError (base)
    ├── DomainError
    │     └── (Ingestion BC errors)
    │           NEWS_SOURCE_NOT_FOUND      → 404
    │           FEED_NOT_FOUND             → 404
    │           RAW_ARTICLE_NOT_FOUND      → 404
    │           CATEGORY_NOT_FOUND         → 404
    │           TOPIC_NOT_FOUND            → 404
    │           DUPLICATE_NEWS_SOURCE      → 409
    │           DUPLICATE_FEED_URL         → 409
    │           DUPLICATE_ARTICLE          → 409
    │           HAS_ACTIVE_FEEDS           → 409
    │           NEWS_SOURCE_INACTIVE       → 409
    │           FEED_INACTIVE              → 409
    │           INVALID_SOURCE_URL         → 422
    │           INVALID_ARTICLE_URL        → 422
    │           INVALID_LANGUAGE           → 422
    │           FEED_MAX_RETRIES_EXCEEDED  → 409
    │           FEED_ALREADY_PAUSED        → 409
    │
    ├── ApplicationError
    │     └── ApplicationErrorCode
    │           COMMAND_INVALID            → 422
    │           COMMAND_MISSING_FIELD      → 422
    │           RESOURCE_NOT_FOUND         → 404
    │           OPERATION_FAILED           → 500
    │           TRANSACTION_FAILED         → 500
    │           CONCURRENCY_CONFLICT       → 409
    │
    └── InfrastructureError
          └── (Persistence errors bubble up)
                PersistenceError           → 503
                EntityNotFoundError        → 404
                DuplicateEntityError       → 409
                ConcurrentModificationError → 409
```

## 3. ApplicationErrorCode → HTTP Status (Fast Path)

Since Application Services return `Result[T]` (never raise), the Presentation Layer maps `Error.code` directly:

```python
# exceptions/error_mapper.py

_APPLICATION_CODE_TO_STATUS: dict[str, int] = {
    "COMMAND_INVALID":           422,
    "COMMAND_MISSING_FIELD":     422,
    "RESOURCE_NOT_FOUND":        404,
    "OPERATION_FAILED":          500,
    "TRANSACTION_FAILED":        500,
    "CONCURRENCY_CONFLICT":      409,
}

def map_error_to_status(error: Error) -> int:
    code_value = error.code.value if isinstance(error.code, Enum) else str(error.code)
    return _APPLICATION_CODE_TO_STATUS.get(code_value, 500)
```

## 4. Domain Error Code → HTTP Status (Indirect Path)

Application ErrorMapper already maps `IngestionErrorCode → ApplicationErrorCode`. The chain is:

```
IngestionErrorCode.NEWS_SOURCE_NOT_FOUND
    → ApplicationErrorCode.RESOURCE_NOT_FOUND
    → HTTP 404
```

```
IngestionErrorCode.DUPLICATE_NEWS_SOURCE
    → ApplicationErrorCode.COMMAND_INVALID
    → HTTP 422  (but we want 409!)
```

**PROBLEM**: The current ErrorMapper maps ALL domain "not found" errors to `RESOURCE_NOT_FOUND` and ALL duplicate/validation errors to `COMMAND_INVALID`. This loses the 409 distinction.

**SOLUTION**: Add a Presentation-layer mapper that understands domain error codes directly:

```python
# exceptions/error_mapper.py

_DOMAIN_CODE_TO_STATUS: dict[str, int] = {
    # Not found → 404
    "NEWS_SOURCE_NOT_FOUND":  404,
    "FEED_NOT_FOUND":         404,
    "RAW_ARTICLE_NOT_FOUND":  404,
    "CATEGORY_NOT_FOUND":     404,
    "TOPIC_NOT_FOUND":        404,
    # Duplicates / conflicts → 409
    "DUPLICATE_NEWS_SOURCE":  409,
    "DUPLICATE_FEED_URL":     409,
    "DUPLICATE_ARTICLE":      409,
    "HAS_ACTIVE_FEEDS":       409,
    "NEWS_SOURCE_INACTIVE":   409,
    "FEED_INACTIVE":          409,
    "FEED_MAX_RETRIES_EXCEEDED": 409,
    "FEED_ALREADY_PAUSED":    409,
    "SOURCE_ALREADY_ENABLED": 409,
    "SOURCE_ALREADY_DISABLED": 409,
    "FEED_ALREADY_ENABLED":   409,
    "FEED_ALREADY_DISABLED":  409,
    # Validation → 422
    "INVALID_SOURCE_URL":     422,
    "INVALID_ARTICLE_URL":    422,
    "INVALID_LANGUAGE":       422,
    "INVALID_SYNC_POLICY":    422,
    "INVALID_STATE":          422,
    "VALIDATION_ERROR":       422,
    "INVALID_CATEGORY":       422,
    "CYCLE_DETECTED":         422,
}
```

## 5. RFC 9457 Problem Details Model

```python
# exceptions/problem_details.py
from pydantic import BaseModel

class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs."""
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    error_code: str | None = None  # Custom extension
```

## 6. Exception Handler Registration

```python
# exceptions/handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_exception_handlers(app: FastAPI):
    """Register global exception handlers."""

    @app.exception_handler(PersistenceError)
    async def persistence_error_handler(request: Request, exc: PersistenceError):
        return JSONResponse(
            status_code=503,
            content=ProblemDetail(
                title="Service Unavailable",
                status=503,
                detail=str(exc),
                instance=str(request.url),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ProblemDetail(
                title="Internal Server Error",
                status=500,
                detail="An unexpected error occurred",
                instance=str(request.url),
            ).model_dump(),
        )
```

## 7. Result → Response Mapping

```python
# In router handlers:
def handle_result[T](result: Result[T], resource_name: str) -> T:
    """Map Result to HTTP response or raise appropriate error."""
    if result.is_success:
        return result.value

    error = result.error
    status = map_error_to_http_status(error)

    raise HTTPException(
        status_code=status,
        detail=ProblemDetail(
            title=status_to_title(status),
            status=status,
            detail=error.message,
            error_code=error.code.value if hasattr(error.code, 'value') else str(error.code),
        ).model_dump(),
    )
```

## 8. Exception Propagation Rules

| Layer | Behavior |
|-------|----------|
| Domain | Raises `DomainError` subclasses |
| Application | Catches `DomainError`, returns `Result.failure(Error)` |
| Presentation | Maps `Error.code` → HTTP status + Problem Details |
| Persistence | Raises `PersistenceError` on infrastructure failure |

Application NEVER propagates exceptions to Presentation. All errors are `Result.failure()`.

Presentation catches any leaked exceptions (safety net) and returns 500.

---

*See also: `api-design.md`, `serialization.md`, `presentation-design.md`*
