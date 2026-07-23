"""
Google News RSS — AI/Tech topics from Google News.

Feed URL: https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en
No credentials needed. Public RSS feed.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

GOOGLE_NEWS_SOURCE = SourceDefinition(
    id="google-news-ai",
    provider="google-news",
    technology="rss",
    categories=["ai", "tech", "news"],
    enabled=True,
    priority=10,
    poll_interval=timedelta(minutes=15),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["google-news", "ai", "technology"],
    metadata={
        "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "timeout": "30",
    },
)
