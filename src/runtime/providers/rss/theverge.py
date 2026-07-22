"""
The Verge RSS — The Verge latest articles.

Feed URL: https://www.theverge.com/rss/index.xml
No credentials needed. Public RSS feed.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

THEVERGE_SOURCE = SourceDefinition(
    id="theverge",
    provider="rss",
    technology="rss",
    categories=["tech", "ai", "gaming"],
    enabled=True,
    priority=7,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["theverge", "tech", "culture"],
    metadata={
        "url": "https://www.theverge.com/rss/index.xml",
        "timeout": "30",
    },
)
