"""
Hacker News API — top stories from Hacker News.

API: https://hacker-news.firebaseio.com/v0/
No credentials needed. Public Firebase API.

Strategy:
1. Fetch top story IDs from /topstories.json
2. For each ID, fetch story details from /item/{id}.json
3. Transform to normalized item format

The transform function handles the multi-step fetch inline.
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


async def _hn_transform(
    raw_data: Any, source_id: str, max_items: int = 30,
) -> list[dict[str, str]]:
    """Transform Hacker News top story IDs into full story items.

    Args:
        raw_data: List of story IDs from /topstories.json.
        source_id: Source identifier.
        max_items: Maximum number of stories to fetch.

    Returns:
        List of normalized item dicts.
    """
    if not isinstance(raw_data, list):
        return []

    story_ids = raw_data[:max_items]
    items: list[dict[str, str]] = []

    async with httpx.AsyncClient() as client:
        for story_id in story_ids:
            try:
                resp = await client.get(
                    f"{HN_API_BASE}/item/{story_id}.json",
                    timeout=10,
                )
                resp.raise_for_status()
                story = resp.json()

                if not story or story.get("type") != "story":
                    continue

                url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                title = story.get("title", "No title")
                content_hash = hashlib.sha256(
                    f"{source_id}:{url}".encode()
                ).hexdigest()[:16]

                items.append({
                    "title": title.strip(),
                    "url": url.strip(),
                    "published": datetime.fromtimestamp(
                        story.get("time", 0), tz=timezone.utc,
                    ).isoformat(),
                    "summary": "",
                    "source_id": source_id,
                    "hn_score": str(story.get("score", 0)),
                    "hn_comments": str(story.get("descendants", 0)),
                    "hn_by": story.get("by", ""),
                    "content_hash": content_hash,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                # Skip individual story failures
                continue

    return items


HACKERNEWS_SOURCE = SourceDefinition(
    id="hackernews",
    provider="api",
    technology="api",
    categories=["tech", "programming", "startups"],
    enabled=True,
    priority=9,
    poll_interval=timedelta(minutes=15),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=30),
    default_tags=["hackernews", "tech", "programming"],
    metadata={
        "base_url": f"{HN_API_BASE}/topstories.json",
        "timeout": "30",
        "max_items": "30",
    },
)
