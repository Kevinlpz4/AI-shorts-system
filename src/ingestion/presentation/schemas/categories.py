"""
Category Schemas — Pydantic request/response models for Category API.

Request models VALIDATE ONLY (format). Business rules live in Application/Domain.

Usage::

    from ingestion.presentation.schemas.categories import (
        CreateCategoryRequest, CategoryDetailResponse,
    )
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ingestion.application.commands.category_commands import (
    CreateCategoryCommand,
    UpdateCategoryCommand,
)
from ingestion.application.dto.category_dto import CategoryDetailDTO, CategorySummaryDTO


# ══════════════════════════════════════════════════════════════════════════════
# Request Models
# ══════════════════════════════════════════════════════════════════════════════


class CreateCategoryRequest(BaseModel):
    """POST /api/v1/categories request body."""

    name: str = Field(..., min_length=1, max_length=100, examples=["Technology"])
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern="^[a-z0-9-]+$",
        examples=["technology"],
    )
    parent_id: str | None = Field(None, examples=[None])

    def to_command(self) -> CreateCategoryCommand:
        """Convert to application command."""
        return CreateCategoryCommand(
            name=self.name, slug=self.slug, parent_id=self.parent_id
        )


class UpdateCategoryRequest(BaseModel):
    """PUT /api/v1/categories/{category_id} request body."""

    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(
        None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$"
    )
    parent_id: str | None = Field(None, examples=[None])

    def to_command(self, category_id: str) -> UpdateCategoryCommand:
        """Convert to application command."""
        return UpdateCategoryCommand(
            category_id=category_id,
            name=self.name,
            slug=self.slug,
            parent_id=self.parent_id,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Response Models
# ══════════════════════════════════════════════════════════════════════════════


class CategorySummaryResponse(BaseModel):
    """Category summary in list responses."""

    id: str
    name: str
    slug: str
    is_active: bool

    @classmethod
    def from_dto(cls, dto: CategorySummaryDTO) -> CategorySummaryResponse:
        """Create from CategorySummaryDTO."""
        return cls(**dto.__dict__)


class CategoryDetailResponse(BaseModel):
    """Category detail in single-resource responses."""

    id: str
    name: str
    slug: str
    parent_id: str | None = None
    is_active: bool = True

    @classmethod
    def from_dto(cls, dto: CategoryDetailDTO) -> CategoryDetailResponse:
        """Create from CategoryDetailDTO."""
        return cls(**dto.__dict__)


class PaginatedCategoriesResponse(BaseModel):
    """Paginated list of categories."""

    data: list[CategorySummaryResponse]
    meta: dict
