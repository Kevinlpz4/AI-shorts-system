"""
Crunchyroll News RSS — anime news feed from Crunchyroll.

Feed URL: https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss
No credentials needed. Public RSS feed.
Contains anime news, industry updates, and Crunchyroll announcements.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

CRUNCHYROLL_NEWS_SOURCE = SourceDefinition(
    id="crunchyroll-news",
    provider="crunchyroll",
    technology="rss",
    categories=["anime", "news", "entertainment"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["crunchyroll", "anime", "news"],
    metadata={
        "url": "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss",
        "timeout": "30",
    },
)
