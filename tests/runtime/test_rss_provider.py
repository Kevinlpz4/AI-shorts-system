"""
Tests for RSS TechnologyAdapter — RSSProvider.

Covers:
- RSS feed parsing with valid feed
- Retry logic on failure
- Missing URL raises ValueError
- Entry normalization
- Empty feed handling
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.providers.rss.rss_provider import RSSProvider


def _make_feedparser_entry(
    title: str = "Test Article",
    link: str = "https://example.com/article/1",
    summary: str = "A test summary",
    published: str = "Mon, 01 Jan 2024 00:00:00 GMT",
) -> MagicMock:
    """Create a mock feedparser entry."""
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.published = published
    entry.updated = ""
    return entry


def _make_parsed_feed(
    entries: list[MagicMock] | None = None,
    bozo: bool = False,
    bozo_exception: Exception | None = None,
) -> MagicMock:
    """Create a mock feedparser parsed result."""
    parsed = MagicMock()
    parsed.entries = entries if entries is not None else []
    parsed.bozo = bozo
    parsed.bozo_exception = bozo_exception
    return parsed


class TestRSSProvider:
    """Tests for RSSProvider TechnologyAdapter."""

    def test_name_property(self) -> None:
        """RSSProvider has name 'rss'."""
        provider = RSSProvider()
        assert provider.name == "rss"

    def test_fetch_requires_url(self) -> None:
        """RSSProvider raises ValueError when 'url' missing from config."""
        provider = RSSProvider()

        with pytest.raises(ValueError, match="requires 'url'"):
            import asyncio
            asyncio.run(provider.fetch("test-source", {}))

    @pytest.mark.asyncio
    async def test_fetch_parses_feed(self) -> None:
        """RSSProvider parses a valid RSS feed."""
        provider = RSSProvider()
        entry = _make_feedparser_entry()
        parsed = _make_parsed_feed(entries=[entry])

        with patch("runtime.providers.rss.rss_provider.asyncio") as mock_asyncio:
            loop = AsyncMock()
            loop.run_in_executor = AsyncMock(return_value=parsed)
            mock_asyncio.get_event_loop.return_value = loop
            mock_asyncio.wait_for = AsyncMock(return_value=parsed)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "test-source",
                {"url": "https://example.com/feed.xml"},
            )

        assert len(items) == 1
        assert items[0]["title"] == "Test Article"
        assert items[0]["url"] == "https://example.com/article/1"
        assert items[0]["source_id"] == "test-source"
        assert "content_hash" in items[0]
        assert "fetched_at" in items[0]

    @pytest.mark.asyncio
    async def test_fetch_handles_empty_feed(self) -> None:
        """RSSProvider handles feed with no entries."""
        provider = RSSProvider()
        parsed = _make_parsed_feed(entries=[])

        with patch("runtime.providers.rss.rss_provider.asyncio") as mock_asyncio:
            loop = AsyncMock()
            loop.run_in_executor = AsyncMock(return_value=parsed)
            mock_asyncio.get_event_loop.return_value = loop
            mock_asyncio.wait_for = AsyncMock(return_value=parsed)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "test-source",
                {"url": "https://example.com/feed.xml"},
            )

        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_skips_entries_without_link(self) -> None:
        """RSSProvider skips entries that lack a link/URL."""
        provider = RSSProvider()
        good_entry = _make_feedparser_entry(link="https://example.com/1")
        bad_entry = _make_feedparser_entry(link="")
        # Make link attribute None for the bad entry
        bad_entry.link = None
        parsed = _make_parsed_feed(entries=[good_entry, bad_entry])

        with patch("runtime.providers.rss.rss_provider.asyncio") as mock_asyncio:
            loop = AsyncMock()
            loop.run_in_executor = AsyncMock(return_value=parsed)
            mock_asyncio.get_event_loop.return_value = loop
            mock_asyncio.wait_for = AsyncMock(return_value=parsed)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "test-source",
                {"url": "https://example.com/feed.xml"},
            )

        assert len(items) == 1
        assert items[0]["url"] == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_fetch_retry_on_failure(self) -> None:
        """RSSProvider retries on failure and succeeds."""
        provider = RSSProvider()
        entry = _make_feedparser_entry()
        parsed = _make_parsed_feed(entries=[entry])

        call_count = 0

        async def mock_wait_for(coro_or_func, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection failed")
            return parsed

        with patch("runtime.providers.rss.rss_provider.asyncio") as mock_asyncio:
            mock_asyncio.wait_for = AsyncMock(side_effect=mock_wait_for)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "test-source",
                {"url": "https://example.com/feed.xml", "retry_delay": 0},
            )

        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_fetch_exhausts_retries(self) -> None:
        """RSSProvider raises RuntimeError after exhausting retries."""
        provider = RSSProvider()

        async def always_fail(coro_or_func, **kwargs):
            raise ConnectionError("Connection failed")

        with patch("runtime.providers.rss.rss_provider.asyncio") as mock_asyncio:
            mock_asyncio.wait_for = AsyncMock(side_effect=always_fail)
            mock_asyncio.sleep = AsyncMock()

            with pytest.raises(RuntimeError, match="failed after"):
                await provider.fetch(
                    "test-source",
                    {"url": "https://example.com/feed.xml", "max_retries": 1, "retry_delay": 0},
                )

    def test_normalize_entry_basic(self) -> None:
        """RSSProvider normalizes a basic entry correctly."""
        provider = RSSProvider()
        entry = _make_feedparser_entry()

        item = provider._normalize_entry("src", entry)

        assert item is not None
        assert item["title"] == "Test Article"
        assert item["url"] == "https://example.com/article/1"
        assert item["source_id"] == "src"
        assert len(item["content_hash"]) == 16

    def test_normalize_entry_no_link(self) -> None:
        """RSSProvider returns None for entry without link."""
        provider = RSSProvider()
        entry = MagicMock()
        entry.link = None

        item = provider._normalize_entry("src", entry)
        assert item is None
