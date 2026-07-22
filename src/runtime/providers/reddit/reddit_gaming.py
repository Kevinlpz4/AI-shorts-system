"""
Reddit Gaming — aggregation of gaming-related subreddits.

Subreddits: r/gaming, r/pcgaming, r/nintendo
No credentials needed. Public RSS feeds.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

REDDIT_GAMING_SOURCE = SourceDefinition(
    id="reddit-gaming",
    provider="reddit",
    technology="reddit",
    categories=["gaming", "pc", "nintendo"],
    enabled=True,
    priority=6,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["reddit", "gaming", "community"],
    metadata={
        "subreddits": "gaming,pcgaming,nintendo",
        "timeout": "30",
        "limit": "25",
    },
)
