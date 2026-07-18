"""
Tests for IngestionEventAdapter — translates Ingestion events into Learning commands.

Validates: command generation from events, None returns for missing data,
and correct command construction.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from learning.integration.adapters.ingestion_adapter import IngestionEventAdapter
from learning.integration.events.ingestion_events import (
    ArticleCreated,
    FeedRegistered,
    RawArticleCollected,
    RawArticleRejected,
    SourceRegistered,
)
from learning.application.commands.signal_commands import RegisterSignalCommand
from learning.application.commands.source_commands import UpdateSourceProfileCommand


class TestHandleRawArticleCollected:
    """Convert article collection into signal registration command."""

    def test_returns_register_signal_command(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected(
            article_id="art-001",
            source_name="Reuters",
            title="Test",
        )
        command = adapter.handle_raw_article_collected(event)
        assert isinstance(command, RegisterSignalCommand)

    def test_command_dimension_is_source(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected(source_name="Reuters")
        command = adapter.handle_raw_article_collected(event)
        assert command is not None
        assert command.dimension == "SOURCE"

    def test_command_value_is_neutral(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected(source_name="Reuters")
        command = adapter.handle_raw_article_collected(event)
        assert command is not None
        assert command.value == 0.5

    def test_command_source_matches_event(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected(source_name="TechBlog")
        command = adapter.handle_raw_article_collected(event)
        assert command is not None
        assert command.source == "TechBlog"

    def test_returns_none_when_no_source_name(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected(source_name="")
        command = adapter.handle_raw_article_collected(event)
        assert command is None

    def test_returns_none_when_source_name_not_set(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleCollected()
        command = adapter.handle_raw_article_collected(event)
        assert command is None


class TestHandleRawArticleRejected:
    """Convert article rejection into source profile update."""

    def test_returns_update_source_profile_command(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleRejected(
            article_id="art-002",
            source_name="SpamBlog",
            reason="Duplicate content",
        )
        command = adapter.handle_raw_article_rejected(event)
        assert isinstance(command, UpdateSourceProfileCommand)

    def test_command_source_id_matches_event(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleRejected(source_name="SpamBlog")
        command = adapter.handle_raw_article_rejected(event)
        assert command is not None
        assert command.source_id == "SpamBlog"

    def test_command_decision_is_rejected(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleRejected(source_name="SpamBlog")
        command = adapter.handle_raw_article_rejected(event)
        assert command is not None
        assert command.decision == "rejected"

    def test_returns_none_when_no_source_name(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleRejected(source_name="")
        command = adapter.handle_raw_article_rejected(event)
        assert command is None

    def test_returns_none_when_source_name_not_set(self) -> None:
        adapter = IngestionEventAdapter()
        event = RawArticleRejected()
        command = adapter.handle_raw_article_rejected(event)
        assert command is None


class TestHandleSourceRegistered:
    """Source registration — no command needed yet."""

    def test_returns_none(self) -> None:
        adapter = IngestionEventAdapter()
        event = SourceRegistered(
            source_id="src-001",
            source_name="Reuters",
            source_type="rss",
        )
        result = adapter.handle_source_registered(event)
        assert result is None

    def test_returns_none_with_defaults(self) -> None:
        adapter = IngestionEventAdapter()
        event = SourceRegistered()
        result = adapter.handle_source_registered(event)
        assert result is None


class TestHandleArticleCreated:
    """Convert article creation into signal registration."""

    def test_returns_register_signal_command(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated(
            article_id="art-010",
            source_name="Reuters",
            title="AI Breakthrough",
        )
        command = adapter.handle_article_created(event)
        assert isinstance(command, RegisterSignalCommand)

    def test_command_dimension_is_source(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated(source_name="Reuters")
        command = adapter.handle_article_created(event)
        assert command is not None
        assert command.dimension == "SOURCE"

    def test_command_value_is_neutral(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated(source_name="Reuters")
        command = adapter.handle_article_created(event)
        assert command is not None
        assert command.value == 0.5

    def test_command_source_matches_event(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated(source_name="TechBlog")
        command = adapter.handle_article_created(event)
        assert command is not None
        assert command.source == "TechBlog"

    def test_returns_none_when_no_source_name(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated(source_name="")
        command = adapter.handle_article_created(event)
        assert command is None

    def test_returns_none_when_source_name_not_set(self) -> None:
        adapter = IngestionEventAdapter()
        event = ArticleCreated()
        command = adapter.handle_article_created(event)
        assert command is None


class TestIngestionEventAdapterConstruction:
    """Adapter initialization and on_recommend callback."""

    def test_default_construction(self) -> None:
        adapter = IngestionEventAdapter()
        assert adapter._on_recommend is None

    def test_construction_with_callback(self) -> None:
        callback = MagicMock()
        adapter = IngestionEventAdapter(on_recommend=callback)
        assert adapter._on_recommend is callback
