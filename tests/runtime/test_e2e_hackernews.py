"""
E2E test for Hacker News API — real external call.

Validates:
- HN Firebase API is reachable
- Top stories can be fetched
- At least 1 valid story is returned
- Story has required fields
"""
from __future__ import annotations


import httpx
import pytest

from runtime.providers.api.hackernews import _hn_transform


@pytest.mark.asyncio
async def test_hackernews_api_e2e() -> None:
    """E2E: Fetch real Hacker News top stories."""
    # Step 1: Fetch top story IDs
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=30,
        )
        resp.raise_for_status()
        top_ids = resp.json()

    assert len(top_ids) > 0, "HN should return at least 1 story ID"

    # Step 2: Transform first 5 stories (limit for test speed)
    items = await _hn_transform(top_ids[:5], "hackernews-e2e", max_items=5)

    assert len(items) >= 1, f"Expected at least 1 story, got {len(items)}"

    # Validate first item
    first = items[0]
    assert first["title"], "Story must have a title"
    assert first["url"].startswith("http"), "Story must have a URL"
    assert first["source_id"] == "hackernews-e2e"
    assert "hn_score" in first, "Story must have hn_score"
    assert "hn_by" in first, "Story must have hn_by"

    print(f"✅ Hacker News API: {len(items)} stories fetched successfully")
    print(f"   First story: {first['title'][:80]}...")
    print(f"   Score: {first['hn_score']}, By: {first['hn_by']}")
