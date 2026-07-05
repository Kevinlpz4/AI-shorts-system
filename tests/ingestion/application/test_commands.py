"""Tests for all Command dataclasses — 15 commands, 4 files."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ingestion.application.commands import (
    ActivateFeedCommand,
    AssignCategoryToFeedCommand,
    AssignCategoryToSourceCommand,
    AssignTopicToFeedCommand,
    AssignTopicToSourceCommand,
    CreateRawArticleCommand,
    DisableSourceCommand,
    EnableSourceCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
    RegisterSourceCommand,
    UpdateFeedCommand,
    UpdateSourceCommand,
)


class TestRegisterSourceCommand:
    """RegisterSourceCommand — Crear nueva fuente."""

    def test_creates_with_all_fields(self) -> None:
        cmd = RegisterSourceCommand(
            name="Reddit",
            source_type="RSS",
            source_url="https://reddit.com/r/programming",
        )
        assert cmd.name == "Reddit"
        assert cmd.source_type == "RSS"
        assert cmd.source_url == "https://reddit.com/r/programming"

    def test_is_frozen(self) -> None:
        cmd = RegisterSourceCommand(name="Test", source_type="RSS", source_url="https://x.com")
        with pytest.raises(FrozenInstanceError):
            cmd.name = "Changed"  # type: ignore[misc]


class TestUpdateSourceCommand:
    """UpdateSourceCommand — Actualizar fuente existente."""

    def test_requires_only_source_id(self) -> None:
        cmd = UpdateSourceCommand(source_id="src-1")
        assert cmd.source_id == "src-1"
        assert cmd.name is None
        assert cmd.source_type is None
        assert cmd.source_url is None

    def test_creates_with_all_optional_fields(self) -> None:
        cmd = UpdateSourceCommand(
            source_id="src-1",
            name="New Name",
            source_type="API",
            source_url="https://new-url.com",
        )
        assert cmd.name == "New Name"
        assert cmd.source_type == "API"
        assert cmd.source_url == "https://new-url.com"


class TestEnableSourceCommand:
    """EnableSourceCommand — Habilitar fuente."""

    def test_creates(self) -> None:
        cmd = EnableSourceCommand(source_id="src-1")
        assert cmd.source_id == "src-1"


class TestDisableSourceCommand:
    """DisableSourceCommand — Deshabilitar fuente."""

    def test_creates_with_reason(self) -> None:
        cmd = DisableSourceCommand(source_id="src-1", reason="Maintenance")
        assert cmd.source_id == "src-1"
        assert cmd.reason == "Maintenance"


class TestRegisterFeedCommand:
    """RegisterFeedCommand — Crear nuevo feed."""

    def test_creates_with_required_only(self) -> None:
        cmd = RegisterFeedCommand(
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech News",
            language="en",
        )
        assert cmd.source_id == "src-1"
        assert cmd.url == "https://example.com/feed"
        assert cmd.label == "Tech News"
        assert cmd.language == "en"
        assert cmd.sync_mode == "PULL"
        assert cmd.sync_interval_minutes == 30
        assert cmd.sync_max_retries == 3
        assert cmd.categories == ()
        assert cmd.topics == ()

    def test_creates_with_categories_and_topics(self) -> None:
        cmd = RegisterFeedCommand(
            source_id="src-1",
            url="https://example.com/feed",
            label="Tech",
            language="en",
            sync_mode="PUSH",
            sync_interval_minutes=None,
            sync_max_retries=5,
            categories=("cat-1", "cat-2"),
            topics=("top-1",),
        )
        assert cmd.categories == ("cat-1", "cat-2")
        assert cmd.topics == ("top-1",)
        assert cmd.sync_mode == "PUSH"


class TestUpdateFeedCommand:
    """UpdateFeedCommand — Actualizar feed existente."""

    def test_requires_only_feed_id(self) -> None:
        cmd = UpdateFeedCommand(feed_id="feed-1")
        assert cmd.feed_id == "feed-1"
        assert cmd.url is None
        assert cmd.label is None
        assert cmd.language is None

    def test_creates_with_all_fields(self) -> None:
        cmd = UpdateFeedCommand(
            feed_id="feed-1",
            url="https://new-url.com/feed",
            label="New Label",
            language="es",
            sync_mode="MANUAL",
            sync_interval_minutes=60,
            sync_max_retries=5,
        )
        assert cmd.url == "https://new-url.com/feed"
        assert cmd.sync_mode == "MANUAL"
        assert cmd.sync_interval_minutes == 60
        assert cmd.sync_max_retries == 5


class TestPauseFeedCommand:
    """PauseFeedCommand — Pausar feed."""

    def test_creates(self) -> None:
        cmd = PauseFeedCommand(feed_id="feed-1", reason="Rate limit")
        assert cmd.feed_id == "feed-1"
        assert cmd.reason == "Rate limit"


class TestActivateFeedCommand:
    """ActivateFeedCommand — Reactivar feed."""

    def test_creates(self) -> None:
        cmd = ActivateFeedCommand(feed_id="feed-1")
        assert cmd.feed_id == "feed-1"


class TestRecordCollectionCommand:
    """RecordCollectionCommand — Registrar fetch exitoso."""

    def test_creates_with_required_only(self) -> None:
        cmd = RecordCollectionCommand(feed_id="feed-1", count=5)
        assert cmd.feed_id == "feed-1"
        assert cmd.count == 5
        assert cmd.batch_id is None

    def test_creates_with_batch_id(self) -> None:
        cmd = RecordCollectionCommand(feed_id="feed-1", count=0, batch_id="batch-abc")
        assert cmd.batch_id == "batch-abc"

    def test_zero_count_is_valid(self) -> None:
        cmd = RecordCollectionCommand(feed_id="feed-1", count=0)
        assert cmd.count == 0


class TestRecordFailureCommand:
    """RecordFailureCommand — Registrar fallo de fetch."""

    def test_creates(self) -> None:
        cmd = RecordFailureCommand(feed_id="feed-1", error="Connection timeout")
        assert cmd.feed_id == "feed-1"
        assert cmd.error == "Connection timeout"


class TestAssignCategoryToSourceCommand:
    """AssignCategoryToSourceCommand — Asignar categoría a source."""

    def test_creates(self) -> None:
        cmd = AssignCategoryToSourceCommand(source_id="src-1", category_id="cat-1")
        assert cmd.source_id == "src-1"
        assert cmd.category_id == "cat-1"


class TestAssignTopicToSourceCommand:
    """AssignTopicToSourceCommand — Asignar topic a source."""

    def test_creates(self) -> None:
        cmd = AssignTopicToSourceCommand(source_id="src-1", topic_id="top-1")
        assert cmd.source_id == "src-1"
        assert cmd.topic_id == "top-1"


class TestAssignCategoryToFeedCommand:
    """AssignCategoryToFeedCommand — Asignar categoría a feed."""

    def test_creates(self) -> None:
        cmd = AssignCategoryToFeedCommand(feed_id="feed-1", category_id="cat-1")
        assert cmd.feed_id == "feed-1"
        assert cmd.category_id == "cat-1"


class TestAssignTopicToFeedCommand:
    """AssignTopicToFeedCommand — Asignar topic a feed."""

    def test_creates(self) -> None:
        cmd = AssignTopicToFeedCommand(feed_id="feed-1", topic_id="top-1")
        assert cmd.feed_id == "feed-1"
        assert cmd.topic_id == "top-1"


class TestCreateRawArticleCommand:
    """CreateRawArticleCommand — Crear artículo crudo."""

    def test_creates_with_required_only(self) -> None:
        cmd = CreateRawArticleCommand(
            feed_id="feed-1",
            external_id="ext-123",
            content_hash="a" * 64,
            title="Test Article",
            url="https://example.com/article",
        )
        assert cmd.feed_id == "feed-1"
        assert cmd.external_id == "ext-123"
        assert cmd.content_hash == "a" * 64
        assert cmd.title == "Test Article"
        assert cmd.url == "https://example.com/article"
        assert cmd.author is None
        assert cmd.language is None
        assert cmd.published_at is None
        assert cmd.fetched_at is None
        assert cmd.content_preview is None
        assert cmd.metadata is None

    def test_creates_with_all_optional_fields(self) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        cmd = CreateRawArticleCommand(
            feed_id="feed-1",
            external_id="ext-123",
            content_hash="b" * 64,
            title="Full Article",
            url="https://example.com/article",
            author="John Doe",
            language="en",
            published_at=now,
            fetched_at=now,
            content_preview="A preview...",
            metadata={"source": "test"},
        )
        assert cmd.author == "John Doe"
        assert cmd.language == "en"
        assert cmd.published_at == now
        assert cmd.fetched_at == now
        assert cmd.content_preview == "A preview..."
        assert cmd.metadata == {"source": "test"}

    def test_is_frozen(self) -> None:
        cmd = CreateRawArticleCommand(
            feed_id="feed-1",
            external_id="ext-123",
            content_hash="c" * 64,
            title="Test",
            url="https://example.com/test",
        )
        with pytest.raises(FrozenInstanceError):
            cmd.title = "Changed"  # type: ignore[misc]


class TestCommandImmutability:
    """All commands must be frozen dataclasses."""

    @pytest.mark.parametrize(
        "cmd_factory",
        [
            lambda: RegisterSourceCommand(name="A", source_type="RSS", source_url="https://x.com"),
            lambda: EnableSourceCommand(source_id="x"),
            lambda: DisableSourceCommand(source_id="x", reason="r"),
            lambda: UpdateSourceCommand(source_id="x"),
            lambda: RegisterFeedCommand(source_id="x", url="https://x.com/f", label="L", language="en"),
            lambda: UpdateFeedCommand(feed_id="x"),
            lambda: PauseFeedCommand(feed_id="x", reason="r"),
            lambda: ActivateFeedCommand(feed_id="x"),
            lambda: RecordCollectionCommand(feed_id="x", count=0),
            lambda: RecordFailureCommand(feed_id="x", error="e"),
            lambda: AssignCategoryToSourceCommand(source_id="x", category_id="y"),
            lambda: AssignTopicToSourceCommand(source_id="x", topic_id="y"),
            lambda: AssignCategoryToFeedCommand(feed_id="x", category_id="y"),
            lambda: AssignTopicToFeedCommand(feed_id="x", topic_id="y"),
            lambda: CreateRawArticleCommand(
                feed_id="x", external_id="e", content_hash="a" * 64, title="T", url="https://x.com/a"
            ),
        ],
    )
    def test_all_commands_are_frozen(self, cmd_factory) -> None:
        cmd = cmd_factory()
        first_field = next(iter(cmd.__dataclass_fields__))
        with pytest.raises(FrozenInstanceError):
            setattr(cmd, first_field, "mutated")
