"""
Steam News RSS — Steam store community news feed.

Feed URL: https://store.steampowered.com/feeds/news/
No credentials needed. Public RSS feed.
Contains aggregated gaming news from Steam community and partners.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

STEAM_NEWS_SOURCE = SourceDefinition(
    id="steam-news",
    provider="rss",
    technology="rss",
    categories=["gaming", "pc", "releases", "updates"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["steam", "gaming", "pc"],
    metadata={
        "url": "https://store.steampowered.com/feeds/news/",
        "timeout": "30",
    },
)
