"""
TechCrunch RSS — TechCrunch latest articles.

Feed URL: https://techcrunch.com/feed/
No credentials needed. Public RSS feed.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

TECHCRUNCH_SOURCE = SourceDefinition(
    id="techcrunch",
    provider="rss",
    technology="rss",
    categories=["tech", "startups", "ai"],
    enabled=True,
    priority=7,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["techcrunch", "tech", "startups"],
    metadata={
        "url": "https://techcrunch.com/feed/",
        "timeout": "30",
    },
)
