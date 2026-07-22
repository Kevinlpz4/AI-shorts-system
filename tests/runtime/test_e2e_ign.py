"""
E2E test for IGN RSS — real external call.

Validates:
- IGN RSS feed is reachable via FeedBurner
- Feed can be parsed
- At least 1 valid item is returned
- Item has required fields
"""
from __future__ import annotations

import pytest

from runtime.providers.rss.rss_provider import RSSProvider


@pytest.mark.asyncio
async def test_ign_rss_e2e() -> None:
    """E2E: Fetch real IGN RSS feed."""
    provider = RSSProvider()

    items = await provider.fetch(
        "ign-e2e",
        {
            "url": "https://feeds.feedburner.com/ign/all",
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
    assert first["source_id"] == "ign-e2e"
    assert first["content_hash"], "Item must have a content_hash"
    assert first["fetched_at"], "Item must have fetched_at"

    print(f"✅ IGN RSS: {len(items)} items fetched successfully")
    print(f"   First item: {first['title'][:80]}...")
