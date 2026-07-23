"""
PlayStation Blog RSS — official PlayStation news feed.

Feed URL: https://blog.playstation.com/feed/
No credentials needed. Public RSS feed.
Contains official PlayStation news, game announcements, and blog posts.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

PLAYSTATION_BLOG_SOURCE = SourceDefinition(
    id="playstation-blog",
    provider="playstation",
    technology="rss",
    categories=["gaming", "playstation", "ps5", "exclusive"],
    enabled=True,
    priority=7,
    poll_interval=timedelta(minutes=30),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["playstation", "ps5", "gaming", "official"],
    metadata={
        "url": "https://blog.playstation.com/feed/",
        "timeout": "30",
    },
)
