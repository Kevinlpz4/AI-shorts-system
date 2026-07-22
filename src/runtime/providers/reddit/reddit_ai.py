"""
Reddit AI — aggregation of AI-related subreddits.

Subreddits: r/artificial, r/OpenAI, r/MachineLearning
No credentials needed. Public RSS feeds.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

REDDIT_AI_SOURCE = SourceDefinition(
    id="reddit-ai",
    provider="reddit",
    technology="reddit",
    categories=["ai", "machine-learning", "llm"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["reddit", "ai", "community"],
    metadata={
        "subreddits": "artificial,OpenAI,MachineLearning",
        "timeout": "30",
        "limit": "25",
    },
)
