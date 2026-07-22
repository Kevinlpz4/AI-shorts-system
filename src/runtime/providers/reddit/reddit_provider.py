"""
Reddit TechnologyAdapter — Reddit RSS feed parser.

Reddit exposes public RSS feeds for subreddits at:
    https://www.reddit.com/r/{subreddit}/.rss

This adapter fetches and parses Reddit's RSS feeds. Handles:
- Reddit-specific feed quirks (HTML in summaries, encoding)
- Multiple subreddits per source (comma-separated in config)
- Retry logic with exponential backoff

This is a TECHNOLOGY adapter — handles Reddit-specific parsing only.

Usage::

    from runtime.providers.reddit.reddit_provider import RedditProvider

    reddit = RedditProvider()
    items = await reddit.fetch("reddit_ai", {
        "subreddits": ["artificial", "OpenAI", "MachineLearning"],
    })
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import feedparser

logger = logging.getLogger(__name__)

REDDIT_RSS_BASE = "https://www.reddit.com/r/{subreddit}/.rss"


class RedditProvider:
    """TechnologyAdapter for Reddit RSS feeds.

    Fetches RSS from one or more subreddits, normalizes entries.
    Each item includes subreddit tag in metadata.

    Configuration keys:
        subreddits: List of subreddit names (required).
        timeout: HTTP timeout in seconds (default: 30).
        max_retries: Maximum retry attempts (default: 3).
        retry_delay: Base delay between retries in seconds (default: 2).
        limit: Max items per subreddit (default: 25).
    """

    @property
    def name(self) -> str:
        return "reddit"

    async def fetch(
        self, source_id: str, config: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fetch from one or more subreddits via RSS.

        Args:
            source_id: Source identifier for logging.
            config: Must contain 'subreddits' (list of names).

        Returns:
            List of normalized item dicts from all subreddits combined.
        """
        subreddits = config.get("subreddits", [])
        if not subreddits:
            raise ValueError(
                f"RedditProvider requires 'subreddits' in config for source '{source_id}'"
            )

        timeout = config.get("timeout", 30)
        max_retries = config.get("max_retries", 3)
        retry_delay = config.get("retry_delay", 2)
        limit = config.get("limit", 25)

        all_items: list[dict[str, str]] = []
        for sub in subreddits:
            url = REDDIT_RSS_BASE.format(subreddit=sub)
            try:
                items = await self._fetch_subreddit(
                    source_id, sub, url, timeout, max_retries, retry_delay, limit,
                )
                all_items.extend(items)
            except Exception as exc:
                logger.warning(
                    "Failed to fetch r/%s for source '%s': %s", sub, source_id, exc,
                )

        logger.info(
            "Fetched %d total items from Reddit source '%s' (%d subreddits)",
            len(all_items),
            source_id,
            len(subreddits),
        )
        return all_items

    async def _fetch_subreddit(
        self,
        source_id: str,
        subreddit: str,
        url: str,
        timeout: int,
        max_retries: int,
        retry_delay: int,
        limit: int,
    ) -> list[dict[str, str]]:
        """Fetch and parse a single subreddit RSS feed."""
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return await self._parse_feed(
                    source_id, subreddit, url, timeout, limit,
                )
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(
                        "Reddit fetch failed r/%s (attempt %d/%d): %s",
                        subreddit,
                        attempt + 1,
                        max_retries + 1,
                        exc,
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"Reddit fetch failed after {max_retries + 1} attempts for "
            f"r/{subreddit}: {last_error}"
        )

    async def _parse_feed(
        self,
        source_id: str,
        subreddit: str,
        url: str,
        timeout: int,
        limit: int,
    ) -> list[dict[str, str]]:
        """Parse a single subreddit RSS feed."""
        loop = asyncio.get_event_loop()
        parsed = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, url),
            timeout=timeout,
        )

        if parsed.bozo and not parsed.entries:
            raise RuntimeError(
                f"Reddit feed parse error for r/{subreddit}: "
                f"{parsed.bozo_exception}"
            )

        items = []
        for entry in parsed.entries[:limit]:
            item = self._normalize_entry(source_id, subreddit, entry)
            if item:
                items.append(item)

        return items

    def _normalize_entry(
        self,
        source_id: str,
        subreddit: str,
        entry: Any,
    ) -> dict[str, str] | None:
        """Normalize a Reddit RSS entry."""
        url = getattr(entry, "link", None)
        if not url:
            return None

        title = getattr(entry, "title", "No title")
        summary = getattr(entry, "summary", "")
        published = getattr(entry, "published", "") or getattr(entry, "updated", "")

        content_hash = hashlib.sha256(
            f"{source_id}:{url}".encode()
        ).hexdigest()[:16]

        return {
            "title": title.strip(),
            "url": url.strip(),
            "published": published,
            "summary": summary[:500] if summary else "",
            "source_id": source_id,
            "subreddit": subreddit,
            "content_hash": content_hash,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
