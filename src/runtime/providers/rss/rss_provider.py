"""
RSS TechnologyAdapter — generic RSS/Atom feed parser.

Uses `feedparser` to parse any RSS or Atom feed URL. Handles:
- Standard RSS 2.0 and Atom feeds
- Retry logic with exponential backoff
- Rate limiting
- Timeout configuration

This is a TECHNOLOGY adapter — no provider-specific logic.

Usage::

    from runtime.providers.rss.rss_provider import RSSProvider

    rss = RSSProvider()
    items = await rss.fetch("techcrunch", {"url": "https://techcrunch.com/feed/"})
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import feedparser

logger = logging.getLogger(__name__)


class RSSProvider:
    """TechnologyAdapter for RSS/Atom feeds.

    Generic RSS fetcher — fetches and parses any RSS/Atom feed URL.
    Returns normalized item dicts with: title, url, published, summary, source_id.

    Configuration keys:
        url: Feed URL (required).
        timeout: HTTP timeout in seconds (default: 30).
        max_retries: Maximum retry attempts (default: 3).
        retry_delay: Base delay between retries in seconds (default: 2).
    """

    @property
    def name(self) -> str:
        return "rss"

    async def fetch(
        self, source_id: str, config: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fetch and parse an RSS/Atom feed.

        Args:
            source_id: Source identifier for logging and item tagging.
            config: Must contain 'url'. Optional: timeout, max_retries, retry_delay.

        Returns:
            List of normalized item dicts.

        Raises:
            ValueError: If 'url' is missing from config.
            RuntimeError: If all retries are exhausted.
        """
        url = config.get("url")
        if not url:
            raise ValueError(f"RSSProvider requires 'url' in config for source '{source_id}'")

        timeout = config.get("timeout", 30)
        max_retries = config.get("max_retries", 3)
        retry_delay = config.get("retry_delay", 2)

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return await self._fetch_feed(source_id, url, timeout)
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(
                        "RSS fetch failed for %s (attempt %d/%d): %s. "
                        "Retrying in %ds...",
                        source_id,
                        attempt + 1,
                        max_retries + 1,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"RSS fetch failed after {max_retries + 1} attempts for "
            f"'{source_id}': {last_error}"
        )

    async def _fetch_feed(
        self, source_id: str, url: str, timeout: int,
    ) -> list[dict[str, str]]:
        """Fetch and parse a single feed attempt.

        feedparser.parse() is synchronous and may block, so we run it
        in a thread executor to keep the event loop responsive.
        """
        loop = asyncio.get_event_loop()
        parsed = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, url),
            timeout=timeout,
        )

        if parsed.bozo and not parsed.entries:
            raise RuntimeError(
                f"Feed parse error for '{source_id}': {parsed.bozo_exception}"
            )

        items = []
        for entry in parsed.entries:
            item = self._normalize_entry(source_id, entry)
            if item:
                items.append(item)

        logger.info("Fetched %d items from RSS source '%s'", len(items), source_id)
        return items

    def _normalize_entry(
        self, source_id: str, entry: Any,
    ) -> dict[str, str] | None:
        """Normalize a feedparser entry to a standard item dict.

        Returns None if the entry lacks a link (URL).
        """
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
            "content_hash": content_hash,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
