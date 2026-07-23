"""
OpenAI Blog RSS — OpenAI official blog feed.

Feed URL: https://openai.com/blog/rss.xml
No credentials needed. Public RSS feed.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

OPENAI_BLOG_SOURCE = SourceDefinition(
    id="openai-blog",
    provider="openai",
    technology="rss",
    categories=["ai", "llm", "company"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(hours=1),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["openai", "blog", "ai"],
    metadata={
        "url": "https://openai.com/blog/rss.xml",
        "timeout": "30",
    },
)
