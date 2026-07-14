"""
Article Schemas — Pydantic request/response models for Article API.

Request models VALIDATE ONLY (format). Business rules live in Application/Domain.

Usage::

    from ingestion.presentation.schemas.articles import (
        CreateArticleRequest, ArticleDetailResponse,
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ingestion.application.commands.article_commands import CreateRawArticleCommand
from ingestion.application.dto.article_dto import RawArticleDetailDTO, RawArticleSummaryDTO


# ══════════════════════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════════════════════


class CreateArticleRequest(BaseModel):
    """POST /api/v1/articles request body."""

    feed_id: str = Field(
        ..., min_length=1, examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    external_id: str = Field(..., min_length=1, examples=["ext-123"])
    content_hash: str = Field(
        ..., min_length=64, max_length=64, examples=["a" * 64]
    )
    title: str = Field(..., min_length=1, max_length=500, examples=["Breaking News"])
    url: str = Field(
        ..., min_length=1, examples=["https://example.com/article/1"]
    )
    author: str | None = Field(None, max_length=200, examples=["John Doe"])
    language: str | None = Field(
        None, pattern="^[a-z]{2}$", examples=["es"]
    )
    published_at: str | None = Field(
        None, examples=["2026-07-10T12:00:00Z"]
    )
    fetched_at: str | None = Field(None, examples=[None])
    content_preview: str | None = Field(
        None, max_length=2000, examples=["Article summary..."]
    )
    metadata: dict | None = Field(None, examples=[None])

    def to_command(self) -> CreateRawArticleCommand:
        """Convert to application command."""
        from datetime import datetime

        pub = (
            datetime.fromisoformat(self.published_at)
            if self.published_at
            else None
        )
        fet = (
            datetime.fromisoformat(self.fetched_at)
            if self.fetched_at
            else None
        )
        return CreateRawArticleCommand(
            feed_id=self.feed_id,
            external_id=self.external_id,
            content_hash=self.content_hash,
            title=self.title,
            url=self.url,
            author=self.author,
            language=self.language,
            published_at=pub,
            fetched_at=fet,
            content_preview=self.content_preview,
            metadata=self.metadata,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════


class ArticleSummaryResponse(BaseModel):
    """Article summary in list responses."""

    id: str
    feed_id: str
    title: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None

    @classmethod
    def from_dto(cls, dto: RawArticleSummaryDTO) -> ArticleSummaryResponse:
        """Create from RawArticleSummaryDTO."""
        return cls(
            id=dto.id,
            feed_id=dto.feed_id,
            title=dto.title,
            url=dto.url,
            author=dto.author,
            language=dto.language,
            published_at=dto.published_at.isoformat() if dto.published_at else None,
            fetched_at=dto.fetched_at.isoformat() if dto.fetched_at else None,
        )


class ArticleDetailResponse(BaseModel):
    """Article detail in single-resource responses."""

    id: str
    feed_id: str
    external_id: str
    content_hash: str
    title: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None
    content_preview: str | None = None
    metadata: dict | None = None

    @classmethod
    def from_dto(cls, dto: RawArticleDetailDTO) -> ArticleDetailResponse:
        """Create from RawArticleDetailDTO."""
        return cls(
            id=dto.id,
            feed_id=dto.feed_id,
            external_id=dto.external_id,
            content_hash=dto.content_hash,
            title=dto.title,
            url=dto.url,
            author=dto.author,
            language=dto.language,
            published_at=dto.published_at.isoformat() if dto.published_at else None,
            fetched_at=dto.fetched_at.isoformat() if dto.fetched_at else None,
            content_preview=dto.content_preview,
            metadata=dto.metadata,
        )


class PaginatedArticlesResponse(BaseModel):
    """Paginated list of articles."""

    data: list[ArticleSummaryResponse]
    meta: dict
