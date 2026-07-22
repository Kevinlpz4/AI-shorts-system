"""
GameSpot RSS — GameSpot all-content feed.

Feed URL: https://www.gamespot.com/feeds/mashup/
No credentials needed. Public RSS feed.
Contains gaming news, reviews, videos, and articles from GameSpot.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

GAMESPOT_SOURCE = SourceDefinition(
    id="gamespot",
    provider="rss",
    technology="rss",
    categories=["gaming", "reviews", "news", "videos"],
    enabled=True,
    priority=7,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["gamespot", "gaming", "reviews"],
    metadata={
        "url": "https://www.gamespot.com/feeds/mashup/",
        "timeout": "30",
    },
)
