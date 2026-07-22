"""
Anthropic Blog RSS — Anthropic official blog feed.

Feed URL: https://www.anthropic.com/rss.xml
No credentials needed. Public RSS feed.
NOTE: If this feed URL is invalid or unreachable, this source will be
disabled at runtime. The feed should be validated during E2E testing.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

ANTHROPIC_SOURCE = SourceDefinition(
    id="anthropic-blog",
    provider="rss",
    technology="rss",
    categories=["ai", "safety", "company"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(hours=1),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["anthropic", "blog", "ai"],
    metadata={
        "url": "https://www.anthropic.com/rss.xml",
        "timeout": "30",
    },
)
