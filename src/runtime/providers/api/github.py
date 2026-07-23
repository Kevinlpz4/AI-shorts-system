"""
GitHub Trending API — recently created high-star repositories.

API: https://api.github.com/search/repositories
No credentials needed for public API, but rate-limited to 10 req/min.

Strategy:
1. Fetch repos created after a date, sorted by stars
2. Transform to normalized item format
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)


def github_transform(
    raw_data: Any, source_id: str,
) -> list[dict[str, str]]:
    """Transform GitHub search results to normalized items.

    Args:
        raw_data: JSON response from GitHub search API.
        source_id: Source identifier.

    Returns:
        List of normalized item dicts.
    """
    if not isinstance(raw_data, dict):
        return []

    items_raw = raw_data.get("items", [])
    items: list[dict[str, str]] = []

    for repo in items_raw:
        if not isinstance(repo, dict):
            continue

        url = repo.get("html_url", "")
        name = repo.get("full_name", "unknown")
        description = repo.get("description", "") or ""
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language", "") or ""
        created = repo.get("created_at", "")

        if not url:
            continue

        content_hash = hashlib.sha256(
            f"{source_id}:{url}".encode()
        ).hexdigest()[:16]

        items.append({
            "title": f"{name} — {description[:100]}" if description else name,
            "url": url,
            "published": created,
            "summary": description[:500],
            "source_id": source_id,
            "gh_stars": str(stars),
            "gh_language": language,
            "gh_name": name,
            "content_hash": content_hash,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    return items


GITHUB_TRENDING_SOURCE = SourceDefinition(
    id="github-trending",
    provider="github",
    technology="api",
    categories=["programming", "open-source", "ai"],
    enabled=True,
    priority=5,
    poll_interval=timedelta(hours=2),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["github", "trending", "open-source"],
    metadata={
        "base_url": "https://api.github.com/search/repositories?q=created:>2026-01-01&sort=stars&order=desc&per_page=20",
        "timeout": "30",
    },
)
