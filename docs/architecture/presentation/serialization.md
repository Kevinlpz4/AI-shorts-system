# Design: Serialization Strategy

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0

---

## 1. Overview

Two serialization layers:

1. **Application DTOs → Pydantic Response models**: Frozen dataclass DTOs are converted to Pydantic models for HTTP response serialization.
2. **Pydantic Request models → Application Commands/Queries**: Pydantic request models are converted to frozen dataclass commands/queries.

```
HTTP Request
    │
    ▼
Pydantic Request Model (snake_case JSON)
    │
    ▼
Frozen Dataclass Command/Query (strings, plain types)
    │
    ▼
Application Service → Result[DTO]
    │
    ▼
Pydantic Response Model (snake_case JSON)
    │
    ▼
HTTP Response
```

## 2. Pydantic Model Configuration

```python
# models/base.py
from pydantic import ConfigDict

class BaseModelConfig:
    """Shared Pydantic model configuration."""
    model_config = ConfigDict(
        from_attributes=True,      # Enable ORM mode for .from_orm()
        populate_by_name=True,     # Accept field aliases
        use_enum_values=True,      # Serialize enums as values
        str_strip_whitespace=True, # Auto-strip whitespace
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        },
    )
```

## 3. Type Serialization Rules

| Python Type | JSON Type | Example | Notes |
|------------|-----------|---------|-------|
| `str` | `"string"` | `"TechCrunch"` | Direct |
| `int` | `42` | `42` | Direct |
| `float` | `3.14` | `3.14` | Direct |
| `bool` | `true/false` | `true` | Direct |
| `UUID` | `"string"` | `"550e8400-e29b-41d4-a716-446655440000"` | UUID string |
| `datetime` | `"string"` | `"2026-07-13T14:00:00Z"` | ISO 8601 UTC |
| `Enum` | `"string"` | `"RSS"` | String value |
| `tuple[str, ...]` | `["a", "b"]` | `["tech", "ai"]` | JSON array |
| `dict` | `{...}` | `{"key": "value"}` | JSON object |
| `None` | `null` | `null` | Null |

## 4. Naming Convention

- **JSON**: `snake_case` throughout (matching Python convention)
- **Field aliases**: NOT used (no camelCase translation needed for this API)
- **Consistency**: Application Layer DTOs already use `snake_case` — no conversion needed

## 5. Request Models

```python
# models/requests/source_requests.py
from pydantic import BaseModel, Field
from enum import Enum

class SourceType(str, Enum):
    RSS = "RSS"
    API = "API"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    NEWSLETTER = "NEWSLETTER"

class CreateSourceRequest(BaseModel):
    """Request body for RegisterSource."""
    name: str = Field(..., min_length=1, max_length=200, examples=["TechCrunch"])
    source_type: SourceType = Field(..., examples=["RSS"])
    source_url: str = Field(..., examples=["https://techcrunch.com/feed/"])

class UpdateSourceRequest(BaseModel):
    """Request body for UpdateSource (all fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=200)
    source_type: SourceType | None = None
    source_url: str | None = None

class DisableSourceRequest(BaseModel):
    """Request body for DisableSource."""
    reason: str = Field(..., min_length=1, max_length=500, examples=["Maintenance"])

class AssignCategoryRequest(BaseModel):
    """Request body for category assignment."""
    category_id: str = Field(..., examples=["550e8400-e29b-41d4-a716-446655440000"])

class AssignTopicRequest(BaseModel):
    """Request body for topic assignment."""
    topic_id: str = Field(..., examples=["660e8400-e29b-41d4-a716-446655440000"])
```

## 6. Response Models

```python
# models/responses/source_responses.py
from pydantic import BaseModel, Field

class SourceSummaryResponse(BaseModel):
    """Summary view of a NewsSource."""
    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool

class SourceDetailResponse(BaseModel):
    """Full detail of a NewsSource."""
    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool
    categories: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
```

## 7. Pagination Envelope

```python
# models/responses/paginated.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    status: str = "success"
    data: list[T]
    meta: dict = Field(default_factory=dict)

class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
```

## 8. DTO → Response Conversion

Application DTOs are frozen dataclasses. Response models are Pydantic. Conversion is simple:

```python
# In router handler:
def source_to_response(dto: SourceDetailDTO) -> SourceDetailResponse:
    return SourceDetailResponse(
        id=dto.id,
        name=dto.name,
        source_type=dto.source_type,
        source_url=dto.source_url,
        is_active=dto.is_active,
        categories=list(dto.categories),
        topics=list(dto.topics),
    )
```

Or use Pydantic's `from_attributes` with a thin adapter:

```python
# models/responses/source_responses.py
class SourceDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_dto(cls, dto: SourceDetailDTO) -> "SourceDetailResponse":
        return cls(
            id=dto.id,
            name=dto.name,
            source_type=dto.source_type,
            source_url=dto.source_url,
            is_active=dto.is_active,
            categories=list(dto.categories),
            topics=list(dto.topics),
        )
```

## 9. Validation Rules

| Rule | Implementation | Layer |
|------|---------------|-------|
| Required fields | `Field(...)` in Pydantic | Request |
| String length | `Field(min_length=..., max_length=...)` | Request |
| Enum values | `str, Enum` class | Request |
| URL format | Pydantic `AnyHttpUrl` or custom validator | Request |
| UUID format | Custom validator: `UUID(str)` | Request |
| Optional fields | `Field(None)` | Request |

---

*See also: `api-design.md`, `exception-handling.md`*
