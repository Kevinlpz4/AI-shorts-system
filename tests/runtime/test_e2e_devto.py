"""
E2E test for Dev.to RSS — real external call.

Validates:
- Dev.to RSS feed is reachable
- Feed can be parsed
- At least 1 valid item is returned
- Item has required fields
"""
from __future__ import annotations

import pytest

from runtime.providers.rss.rss_provider import RSSProvider


@pytest.mark.asyncio
async def test_devto_rss_e2e() -> None:
    """E2E: Fetch real Dev.to RSS feed."""
    provider = RSSProvider()

    items = await provider.fetch(
        "devto-e2e",
        {
            "url": "https://dev.to/feed",
            "timeout": 30,
            "max_retries": 2,
        },
    )

    assert len(items) >= 1, f"Expected at least 1 item, got {len(items)}"

    # Validate first item
    first = items[0]
    assert first["title"], "Item must have a title"
    assert first["url"].startswith("http"), "Item must have a URL"
    assert first["source_id"] == "devto-e2e"
    assert first["content_hash"], "Item must have content_hash"

    print(f"✅ Dev.to RSS: {len(items)} items fetched successfully")
    print(f"   First item: {first['title'][:80]}...")
