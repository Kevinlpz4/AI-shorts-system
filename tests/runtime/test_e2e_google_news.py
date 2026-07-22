"""
E2E test for Google News RSS — real external call.

Validates:
- Google News RSS feed is reachable
- Feed can be parsed
- At least 1 valid item is returned
- Item has required fields
"""
from __future__ import annotations

import asyncio

import pytest

from runtime.providers.rss.rss_provider import RSSProvider


@pytest.mark.asyncio
async def test_google_news_rss_e2e() -> None:
    """E2E: Fetch real Google News RSS feed for AI topics."""
    provider = RSSProvider()

    items = await provider.fetch(
        "google-news-e2e",
        {
            "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
            "timeout": 30,
            "max_retries": 2,
        },
    )

    # Must have at least 1 item
    assert len(items) >= 1, f"Expected at least 1 item, got {len(items)}"

    # Validate first item has required fields
    first = items[0]
    assert first["title"], "Item must have a title"
    assert first["url"].startswith("http"), "Item must have a valid URL"
    assert first["source_id"] == "google-news-e2e"
    assert first["content_hash"], "Item must have a content_hash"
    assert first["fetched_at"], "Item must have fetched_at"

    print(f"✅ Google News RSS: {len(items)} items fetched successfully")
    print(f"   First item: {first['title'][:80]}...")
