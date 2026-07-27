"""
Crunchyroll Anime RSS — latest anime episodes feed.

Feed URL: http://feeds.feedburner.com/crunchyroll/rss/anime
No credentials needed. Public RSS feed via FeedBurner.
Contains recently published anime episodes from Crunchyroll catalog.
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import (
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

CRUNCHYROLL_ANIME_SOURCE = SourceDefinition(
    id="crunchyroll-anime",
    provider="crunchyroll",
    technology="rss",
    categories=["anime", "episodes", "entertainment"],
    enabled=True,
    priority=8,
    poll_interval=timedelta(minutes=20),
    retry_policy=RetryPolicy(max_retries=3),
    rate_limit=RateLimitConfig(requests_per_minute=10),
    default_tags=["crunchyroll", "anime", "episodes"],
    metadata={
        "url": "http://feeds.feedburner.com/crunchyroll/rss/anime",
        "timeout": "30",
    },
)
