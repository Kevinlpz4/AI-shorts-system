"""
Reddit Gaming — aggregation of gaming-related subreddits.

Subreddits: Games, gaming, pcgaming, Steam, PS5, NintendoSwitch, XboxSeriesX, GTA6
No credentials needed. Public RSS feeds.

Note: 'nintendo' was replaced with 'NintendoSwitch' (the active subreddit).
      'Games' added as it's the premier quality gaming discussion subreddit.
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
    provider="reddit-gaming",
    technology="reddit",
    categories=["gaming", "pc", "console", "steam", "playstation", "nintendo", "xbox"],
    enabled=True,
    priority=6,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=5),
    default_tags=["reddit", "gaming", "community"],
    metadata={
        "subreddits": "Games,gaming,pcgaming,Steam,PS5,NintendoSwitch,XboxSeriesX,GTA6",
        "timeout": "30",
        "limit": "25",
    },
)
