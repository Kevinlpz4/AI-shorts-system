"""
Dev.to RSS — Dev.to latest articles.

Feed URL: https://dev.to/feed
No credentials needed. Public RSS feed.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

DEVTO_SOURCE = SourceDefinition(
    id="devto",
    provider="devto",
    technology="rss",
    categories=["programming", "tutorials", "tech"],
    enabled=True,
    priority=6,
    poll_interval=timedelta(minutes=30),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["devto", "programming", "community"],
    metadata={
        "url": "https://dev.to/feed",
        "timeout": "30",
    },
)
