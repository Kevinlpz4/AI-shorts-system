"""
Tests for Reddit TechnologyAdapter — RedditProvider.

Covers:
- Single subreddit fetch
- Multiple subreddit fetch
- Missing subreddits raises ValueError
- Retry logic
- Entry normalization with subreddit tag
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.providers.reddit.reddit_provider import RedditProvider


def _make_feedparser_entry(
    title: str = "Reddit Post",
    link: str = "https://reddit.com/r/test/abc123",
    summary: str = "Post body",
    published: str = "Mon, 01 Jan 2024 00:00:00 GMT",
) -> MagicMock:
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.published = published
    entry.updated = ""
    return entry


def _make_parsed_feed(entries=None, bozo=False):
    parsed = MagicMock()
    parsed.entries = entries if entries is not None else []
    parsed.bozo = bozo
    parsed.bozo_exception = None
    return parsed


class TestRedditProvider:
    """Tests for RedditProvider TechnologyAdapter."""

    def test_name_property(self) -> None:
        """RedditProvider has name 'reddit'."""
        provider = RedditProvider()
        assert provider.name == "reddit"

    def test_fetch_requires_subreddits(self) -> None:
        """RedditProvider raises ValueError when 'subreddits' missing."""
        provider = RedditProvider()
        with pytest.raises(ValueError, match="requires 'subreddits'"):
            import asyncio
            asyncio.run(provider.fetch("test-source", {}))

    @pytest.mark.asyncio
    async def test_fetch_single_subreddit(self) -> None:
        """RedditProvider fetches from a single subreddit."""
        provider = RedditProvider()
        entry = _make_feedparser_entry()
        parsed = _make_parsed_feed(entries=[entry])

        with patch("runtime.providers.reddit.reddit_provider.asyncio") as mock_asyncio:
            loop = AsyncMock()
            loop.run_in_executor = AsyncMock(return_value=parsed)
            mock_asyncio.get_event_loop.return_value = loop
            mock_asyncio.wait_for = AsyncMock(return_value=parsed)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "reddit-ai",
                {"subreddits": ["artificial"]},
            )

        assert len(items) == 1
        assert items[0]["subreddit"] == "artificial"
        assert items[0]["source_id"] == "reddit-ai"

    @pytest.mark.asyncio
    async def test_fetch_multiple_subreddits(self) -> None:
        """RedditProvider fetches from multiple subreddits."""
        provider = RedditProvider()
        entry = _make_feedparser_entry()
        parsed = _make_parsed_feed(entries=[entry])

        with patch("runtime.providers.reddit.reddit_provider.asyncio") as mock_asyncio:
            loop = AsyncMock()
            loop.run_in_executor = AsyncMock(return_value=parsed)
            mock_asyncio.get_event_loop.return_value = loop
            mock_asyncio.wait_for = AsyncMock(return_value=parsed)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "reddit-ai",
                {"subreddits": ["artificial", "OpenAI"]},
            )

        # 1 item per subreddit = 2 items
        assert len(items) == 2
        subreddits = {item["subreddit"] for item in items}
        assert subreddits == {"artificial", "OpenAI"}

    @pytest.mark.asyncio
    async def test_fetch_continues_after_subreddit_failure(self) -> None:
        """RedditProvider continues fetching other subreddits if one fails."""
        provider = RedditProvider()
        entry = _make_feedparser_entry()
        parsed = _make_parsed_feed(entries=[entry])

        call_count = 0

        async def mock_wait_for(coro_or_func, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First subreddit: both attempts fail
                raise ConnectionError("Failed")
            return parsed

        with patch("runtime.providers.reddit.reddit_provider.asyncio") as mock_asyncio:
            mock_asyncio.wait_for = AsyncMock(side_effect=mock_wait_for)
            mock_asyncio.sleep = AsyncMock()

            items = await provider.fetch(
                "reddit-ai",
                {"subreddits": ["artificial", "OpenAI"], "max_retries": 1, "retry_delay": 0},
            )

        # Only the second subreddit succeeds
        assert len(items) == 1

    def test_normalize_entry(self) -> None:
        """RedditProvider normalizes entry with subreddit tag."""
        provider = RedditProvider()
        entry = _make_feedparser_entry()

        item = provider._normalize_entry("src", "artificial", entry)

        assert item is not None
        assert item["subreddit"] == "artificial"
        assert item["title"] == "Reddit Post"
        assert "content_hash" in item
