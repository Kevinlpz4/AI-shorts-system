"""
Feed Schemas — Pydantic request/response models for Feed API.

Request models VALIDATE ONLY (format). Business rules live in Application/Domain.

Usage::

    from ingestion.presentation.schemas.feeds import (
        RegisterFeedRequest, FeedDetailResponse,
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
    UpdateFeedCommand,
)
from ingestion.application.commands.feed_category_commands import (
    AssignCategoryToFeedCommand,
    AssignTopicToFeedCommand,
)
from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO


# ══════════════════════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════════════════════


class RegisterFeedRequest(BaseModel):
    """POST /api/v1/feeds request body."""

    source_id: str = Field(
        ..., min_length=1, examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    url: str = Field(
        ..., min_length=1, examples=["https://www.lanacion.com.ar/rss/feed"]
    )
    label: str = Field(
        ..., min_length=1, max_length=200, examples=["La Nación RSS"]
    )
    language: str = Field(
        ..., pattern="^[a-z]{2}$", examples=["es"]
    )
    sync_mode: str = Field(
        default="PULL",
        pattern="^(PULL|PUSH|STREAM|MANUAL)$",
        examples=["PULL"],
    )
    sync_interval_minutes: int | None = Field(
        default=30, ge=1, examples=[30]
    )
    sync_max_retries: int = Field(
        default=3, ge=0, examples=[3]
    )
    categories: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)

    def to_command(self) -> RegisterFeedCommand:
        """Convert to application command."""
        return RegisterFeedCommand(
            source_id=self.source_id,
            url=self.url,
            label=self.label,
            language=self.language,
            sync_mode=self.sync_mode,
            sync_interval_minutes=self.sync_interval_minutes,
            sync_max_retries=self.sync_max_retries,
            categories=tuple(self.categories),
            topics=tuple(self.topics),
        )


class UpdateFeedRequest(BaseModel):
    """PUT /api/v1/feeds/{feed_id} request body."""

    url: str | None = Field(None, min_length=1)
    label: str | None = Field(None, min_length=1, max_length=200)
    language: str | None = Field(None, pattern="^[a-z]{2}$")
    sync_mode: str | None = Field(
        None, pattern="^(PULL|PUSH|STREAM|MANUAL)$"
    )
    sync_interval_minutes: int | None = Field(None, ge=1)
    sync_max_retries: int | None = Field(None, ge=0)

    def to_command(self, feed_id: str) -> UpdateFeedCommand:
        """Convert to application command."""
        return UpdateFeedCommand(
            feed_id=feed_id,
            url=self.url,
            label=self.label,
            language=self.language,
            sync_mode=self.sync_mode,
            sync_interval_minutes=self.sync_interval_minutes,
            sync_max_retries=self.sync_max_retries,
        )


class PauseFeedRequest(BaseModel):
    """POST /api/v1/feeds/{id}/pause request body."""

    reason: str = Field(..., min_length=1, examples=["Manual pause"])


class RecordCollectionRequest(BaseModel):
    """POST /api/v1/feeds/{id}/collect request body."""

    count: int = Field(..., ge=0, examples=[5])
    batch_id: str | None = Field(None, examples=[None])


class RecordFailureRequest(BaseModel):
    """POST /api/v1/feeds/{id}/failure request body."""

    error: str = Field(
        ..., min_length=1, examples=["Connection timeout"]
    )


class AssignCategoryRequest(BaseModel):
    """POST /api/v1/feeds/{id}/categories request body."""

    category_id: str = Field(
        ...,
        min_length=1,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class AssignTopicRequest(BaseModel):
    """POST /api/v1/feeds/{id}/topics request body."""

    topic_id: str = Field(
        ...,
        min_length=1,
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════


class FeedSummaryResponse(BaseModel):
    """Feed summary in list responses."""

    id: str
    source_id: str
    url: str
    label: str
    language: str
    is_active: bool
    retry_count: int = 0

    @classmethod
    def from_dto(cls, dto: FeedSummaryDTO) -> FeedSummaryResponse:
        """Create from FeedSummaryDTO."""
        return cls(**dto.__dict__)


class FeedDetailResponse(BaseModel):
    """Feed detail in single-resource responses."""

    id: str
    source_id: str
    url: str
    label: str
    language: str
    is_active: bool
    sync_mode: str = "PULL"
    sync_interval_minutes: int | None = None
    sync_max_retries: int = 3
    categories: list[str] = []
    topics: list[str] = []
    retry_count: int = 0

    @classmethod
    def from_dto(cls, dto: FeedDetailDTO) -> FeedDetailResponse:
        """Create from FeedDetailDTO."""
        return cls(
            id=dto.id,
            source_id=dto.source_id,
            url=dto.url,
            label=dto.label,
            language=dto.language,
            is_active=dto.is_active,
            sync_mode=dto.sync_mode,
            sync_interval_minutes=dto.sync_interval_minutes,
            sync_max_retries=dto.sync_max_retries,
            categories=list(dto.categories),
            topics=list(dto.topics),
            retry_count=dto.retry_count,
        )


class PaginatedFeedsResponse(BaseModel):
    """Paginated list of feeds."""

    data: list[FeedSummaryResponse]
    meta: dict
