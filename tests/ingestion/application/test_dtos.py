"""Tests for all DTOs — 10 DTOs, 5 files, all frozen."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from ingestion.application.dto import (
    CategoryDetailDTO,
    CategorySummaryDTO,
    FeedDetailDTO,
    FeedSummaryDTO,
    RawArticleDetailDTO,
    RawArticleSummaryDTO,
    SourceDetailDTO,
    SourceSummaryDTO,
    TopicDetailDTO,
    TopicSummaryDTO,
)


class TestSourceSummaryDTO:
    """SourceSummaryDTO — Resumen de NewsSource."""

    def test_creates(self) -> None:
        dto = SourceSummaryDTO(
            id="src-1",
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
            is_active=True,
        )
        assert dto.id == "src-1"
        assert dto.name == "Reddit"
        assert dto.is_active is True

    def test_is_frozen(self) -> None:
        dto = SourceSummaryDTO(
            id="src-1", name="X", source_type="API", source_url="https://x.com", is_active=True
        )
        with pytest.raises(FrozenInstanceError):
            dto.name = "Changed"  # type: ignore[misc]


class TestSourceDetailDTO:
    """SourceDetailDTO — Detalle completo de NewsSource."""

    def test_creates_with_empty_relations(self) -> None:
        dto = SourceDetailDTO(
            id="src-1",
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
            is_active=True,
        )
        assert dto.categories == ()
        assert dto.topics == ()

    def test_creates_with_categories_and_topics(self) -> None:
        dto = SourceDetailDTO(
            id="src-1",
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com",
            is_active=True,
            categories=("cat-1", "cat-2"),
            topics=("top-1",),
        )
        assert dto.categories == ("cat-1", "cat-2")
        assert dto.topics == ("top-1",)


class TestFeedSummaryDTO:
    """FeedSummaryDTO — Resumen de Feed."""

    def test_creates(self) -> None:
        dto = FeedSummaryDTO(
            id="feed-1",
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech News",
            language="en",
            is_active=True,
        )
        assert dto.id == "feed-1"
        assert dto.retry_count == 0

    def test_creates_with_retry_count(self) -> None:
        dto = FeedSummaryDTO(
            id="feed-1",
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech",
            language="en",
            is_active=False,
            retry_count=3,
        )
        assert dto.retry_count == 3
        assert dto.is_active is False


class TestFeedDetailDTO:
    """FeedDetailDTO — Detalle completo de Feed."""

    def test_creates_with_defaults(self) -> None:
        dto = FeedDetailDTO(
            id="feed-1",
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech",
            language="en",
            is_active=True,
        )
        assert dto.sync_mode == "PULL"
        assert dto.sync_interval_minutes is None
        assert dto.sync_max_retries == 3
        assert dto.categories == ()
        assert dto.topics == ()
        assert dto.retry_count == 0

    def test_creates_with_all_fields(self) -> None:
        dto = FeedDetailDTO(
            id="feed-1",
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech",
            language="en",
            is_active=True,
            sync_mode="PUSH",
            sync_interval_minutes=60,
            sync_max_retries=5,
            categories=("cat-1",),
            topics=("top-1", "top-2"),
            retry_count=2,
        )
        assert dto.sync_mode == "PUSH"
        assert dto.sync_interval_minutes == 60
        assert dto.sync_max_retries == 5
        assert dto.categories == ("cat-1",)
        assert dto.topics == ("top-1", "top-2")
        assert dto.retry_count == 2


class TestRawArticleSummaryDTO:
    """RawArticleSummaryDTO — Resumen de RawArticle."""

    def test_creates_with_required_only(self) -> None:
        dto = RawArticleSummaryDTO(
            id="art-1",
            feed_id="feed-1",
            title="Test Article",
            url="https://example.com/article",
        )
        assert dto.id == "art-1"
        assert dto.author is None
        assert dto.language is None
        assert dto.published_at is None
        assert dto.fetched_at is None

    def test_creates_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        dto = RawArticleSummaryDTO(
            id="art-1",
            feed_id="feed-1",
            title="Test",
            url="https://example.com/a",
            author="John",
            language="en",
            published_at=now,
            fetched_at=now,
        )
        assert dto.author == "John"
        assert dto.language == "en"
        assert dto.published_at == now


class TestRawArticleDetailDTO:
    """RawArticleDetailDTO — Detalle completo de RawArticle."""

    def test_creates_with_required_only(self) -> None:
        dto = RawArticleDetailDTO(
            id="art-1",
            feed_id="feed-1",
            external_id="ext-123",
            content_hash="a" * 64,
            title="Test",
            url="https://example.com/a",
        )
        assert dto.author is None
        assert dto.metadata is None
        assert dto.content_preview is None

    def test_creates_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        dto = RawArticleDetailDTO(
            id="art-1",
            feed_id="feed-1",
            external_id="ext-123",
            content_hash="b" * 64,
            title="Full",
            url="https://example.com/full",
            author="Jane",
            language="es",
            published_at=now,
            fetched_at=now,
            content_preview="Preview...",
            metadata={"key": "val"},
        )
        assert dto.content_hash == "b" * 64
        assert dto.author == "Jane"
        assert dto.content_preview == "Preview..."
        assert dto.metadata == {"key": "val"}


class TestCategorySummaryDTO:
    """CategorySummaryDTO — Resumen de Category."""

    def test_creates(self) -> None:
        dto = CategorySummaryDTO(
            id="cat-1",
            name="Technology",
            slug="technology",
            is_active=True,
        )
        assert dto.name == "Technology"
        assert dto.slug == "technology"


class TestCategoryDetailDTO:
    """CategoryDetailDTO — Detalle completo de Category."""

    def test_creates_without_parent(self) -> None:
        dto = CategoryDetailDTO(
            id="cat-1",
            name="Technology",
            slug="technology",
            is_active=True,
        )
        assert dto.parent_id is None

    def test_creates_with_parent(self) -> None:
        dto = CategoryDetailDTO(
            id="cat-2",
            name="Python",
            slug="python",
            parent_id="cat-1",
            is_active=True,
        )
        assert dto.parent_id == "cat-1"


class TestTopicSummaryDTO:
    """TopicSummaryDTO — Resumen de Topic."""

    def test_creates(self) -> None:
        dto = TopicSummaryDTO(id="top-1", name="AI", is_active=True)
        assert dto.name == "AI"
        assert dto.is_active is True


class TestTopicDetailDTO:
    """TopicDetailDTO — Detalle completo de Topic."""

    def test_creates_without_description(self) -> None:
        dto = TopicDetailDTO(id="top-1", name="AI", is_active=True)
        assert dto.description is None

    def test_creates_with_description(self) -> None:
        dto = TopicDetailDTO(id="top-1", name="AI", is_active=True, description="Artificial Intelligence")
        assert dto.description == "Artificial Intelligence"


class TestDTOImmutability:
    """All DTOs must be frozen."""

    @pytest.mark.parametrize(
        "dto_factory",
        [
            lambda: SourceSummaryDTO(id="a", name="N", source_type="RSS", source_url="https://x.com", is_active=True),
            lambda: SourceDetailDTO(id="a", name="N", source_type="RSS", source_url="https://x.com", is_active=True),
            lambda: FeedSummaryDTO(id="a", source_id="b", url="https://x.com/f", label="L", language="en", is_active=True),
            lambda: FeedDetailDTO(id="a", source_id="b", url="https://x.com/f", label="L", language="en", is_active=True),
            lambda: RawArticleSummaryDTO(id="a", feed_id="b", title="T", url="https://x.com/a"),
            lambda: RawArticleDetailDTO(id="a", feed_id="b", external_id="e", content_hash="c" * 64, title="T", url="https://x.com/a"),
            lambda: CategorySummaryDTO(id="a", name="N", slug="n", is_active=True),
            lambda: CategoryDetailDTO(id="a", name="N", slug="n", is_active=True),
            lambda: TopicSummaryDTO(id="a", name="N", is_active=True),
            lambda: TopicDetailDTO(id="a", name="N", is_active=True),
        ],
    )
    def test_all_dtos_are_frozen(self, dto_factory) -> None:
        dto = dto_factory()
        first_field = next(iter(dto.__dataclass_fields__))
        with pytest.raises(FrozenInstanceError):
            setattr(dto, first_field, "mutated")
