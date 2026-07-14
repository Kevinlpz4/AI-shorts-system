"""
Source Schemas — Pydantic request/response models for Source API.

Request models VALIDATE ONLY (format). Business rules live in Application/Domain.

Usage::

    from ingestion.presentation.schemas.sources import (
        RegisterSourceRequest, SourceDetailResponse,
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ingestion.application.commands.source_commands import (
    RegisterSourceCommand,
    UpdateSourceCommand,
)
from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO


# ══════════════════════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════════════════════


class RegisterSourceRequest(BaseModel):
    """POST /api/v1/sources request body."""

    name: str = Field(
        ..., min_length=1, max_length=200, examples=["La Nación"]
    )
    source_type: str = Field(
        ...,
        pattern="^(RSS|API|SOCIAL_MEDIA|NEWSLETTER)$",
        examples=["RSS"],
    )
    source_url: str = Field(
        ..., min_length=1, examples=["https://www.lanacion.com.ar/rss"]
    )

    def to_command(self) -> RegisterSourceCommand:
        """Convert to application command."""
        return RegisterSourceCommand(
            name=self.name,
            source_type=self.source_type,
            source_url=self.source_url,
        )


class UpdateSourceRequest(BaseModel):
    """PUT /api/v1/sources/{source_id} request body."""

    name: str | None = Field(None, min_length=1, max_length=200)
    source_type: str | None = Field(
        None, pattern="^(RSS|API|SOCIAL_MEDIA|NEWSLETTER)$"
    )
    source_url: str | None = Field(None, min_length=1)

    def to_command(self, source_id: str) -> UpdateSourceCommand:
        """Convert to application command."""
        return UpdateSourceCommand(
            source_id=source_id,
            name=self.name,
            source_type=self.source_type,
            source_url=self.source_url,
        )


class DeactivateSourceRequest(BaseModel):
    """POST /api/v1/sources/{id}/deactivate and DELETE body."""

    reason: str = Field(
        ..., min_length=1, examples=["No longer maintained"]
    )


class AssignCategoryRequest(BaseModel):
    """POST /api/v1/sources/{id}/categories request body."""

    category_id: str = Field(
        ...,
        min_length=1,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class AssignTopicRequest(BaseModel):
    """POST /api/v1/sources/{id}/topics request body."""

    topic_id: str = Field(
        ...,
        min_length=1,
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════


class SourceSummaryResponse(BaseModel):
    """Source summary in list responses."""

    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool

    @classmethod
    def from_dto(cls, dto: SourceSummaryDTO) -> SourceSummaryResponse:
        """Create from SourceSummaryDTO."""
        return cls(**dto.__dict__)


class SourceDetailResponse(BaseModel):
    """Source detail in single-resource responses."""

    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool
    categories: list[str] = []
    topics: list[str] = []

    @classmethod
    def from_dto(cls, dto: SourceDetailDTO) -> SourceDetailResponse:
        """Create from SourceDetailDTO."""
        return cls(
            id=dto.id,
            name=dto.name,
            source_type=dto.source_type,
            source_url=dto.source_url,
            is_active=dto.is_active,
            categories=list(dto.categories),
            topics=list(dto.topics),
        )


class PaginatedSourcesResponse(BaseModel):
    """Paginated list of sources."""

    data: list[SourceSummaryResponse]
    meta: dict


class ProblemDetailResponse(BaseModel):
    """RFC 9457 Problem Details (matches ProblemDetail in exceptions.py)."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    error_code: str | None = None
