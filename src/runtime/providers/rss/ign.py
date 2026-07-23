"""
IGN RSS — IGN gaming and entertainment news feed.

Feed URL: https://feeds.feedburner.com/ign/all
No credentials needed. Public RSS feed via FeedBurner.
Contains gaming news, reviews, and entertainment articles from IGN.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

IGN_SOURCE = SourceDefinition(
    id="ign",
    provider="ign",
    technology="rss",
    categories=["gaming", "reviews", "entertainment", "news"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["ign", "gaming", "reviews"],
    metadata={
        "url": "https://feeds.feedburner.com/ign/all",
        "timeout": "30",
    },
)
