"""
Topic Schemas — Pydantic request/response models for Topic API.

Request models VALIDATE ONLY (format). Business rules live in Application/Domain.

Usage::

    from ingestion.presentation.schemas.topics import (
        CreateTopicRequest, TopicDetailResponse,
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ingestion.application.commands.topic_commands import (
    CreateTopicCommand,
    UpdateTopicCommand,
)
from ingestion.application.dto.topic_dto import TopicDetailDTO, TopicSummaryDTO


# ══════════════════════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════════════════════


class CreateTopicRequest(BaseModel):
    """POST /api/v1/topics request body."""

    name: str = Field(..., min_length=1, max_length=200, examples=["AI Trends"])
    description: str | None = Field(
        None, max_length=1000, examples=["Artificial intelligence trends"]
    )

    def to_command(self) -> CreateTopicCommand:
        """Convert to application command."""
        return CreateTopicCommand(name=self.name, description=self.description)


class UpdateTopicRequest(BaseModel):
    """PUT /api/v1/topics/{topic_id} request body."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)

    def to_command(self, topic_id: str) -> UpdateTopicCommand:
        """Convert to application command."""
        return UpdateTopicCommand(
            topic_id=topic_id, name=self.name, description=self.description
        )


# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════


class TopicSummaryResponse(BaseModel):
    """Topic summary in list responses."""

    id: str
    name: str
    is_active: bool

    @classmethod
    def from_dto(cls, dto: TopicSummaryDTO) -> TopicSummaryResponse:
        """Create from TopicSummaryDTO."""
        return cls(**dto.__dict__)


class TopicDetailResponse(BaseModel):
    """Topic detail in single-resource responses."""

    id: str
    name: str
    description: str | None = None
    is_active: bool = True

    @classmethod
    def from_dto(cls, dto: TopicDetailDTO) -> TopicDetailResponse:
        """Create from TopicDetailDTO."""
        return cls(**dto.__dict__)


class PaginatedTopicsResponse(BaseModel):
    """Paginated list of topics."""

    data: list[TopicSummaryResponse]
    meta: dict
