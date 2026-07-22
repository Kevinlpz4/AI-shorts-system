"""
REST API TechnologyAdapter — generic HTTP GET with JSON parsing.

Uses `httpx` for async HTTP. Handles:
- GET requests with JSON response parsing
- Configurable headers, query params
- Retry logic with exponential backoff
- Rate limiting via asyncio.sleep between requests
- Timeout configuration

This is a TECHNOLOGY adapter — no provider-specific logic.

Usage::

    from runtime.providers.api.api_provider import APIProvider

    api = APIProvider()
    items = await api.fetch("hackernews", {
        "base_url": "https://hacker-news.firebaseio.com/v0",
        "endpoints": {"top": "/topstories.json"},
    })
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class APIProvider:
    """TechnologyAdapter for REST API sources.

    Generic HTTP GET with JSON parsing. The `config` dict controls
    everything: URL, headers, query params, pagination, item mapping.

    Configuration keys:
        base_url: Base URL for the API (required).
        headers: Optional HTTP headers dict.
        timeout: HTTP timeout in seconds (default: 30).
        max_retries: Maximum retry attempts (default: 3).
        retry_delay: Base delay between retries in seconds (default: 2).
        rate_limit_delay: Delay between requests in seconds (default: 0).
        transform: Optional callable to transform raw JSON to item dicts.
        items_path: JSON path to the list of items (dot-separated, optional).
        item_fields: Mapping of output field names to JSON paths (optional).
    """

    @property
    def name(self) -> str:
        return "api"

    async def fetch(
        self, source_id: str, config: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fetch data from a REST API endpoint.

        Args:
            source_id: Source identifier for logging.
            config: Must contain 'base_url'. Optional: headers, timeout, etc.

        Returns:
            List of normalized item dicts.
        """
        base_url = config.get("base_url")
        if not base_url:
            raise ValueError(
                f"APIProvider requires 'base_url' in config for source '{source_id}'"
            )

        headers = config.get("headers", {})
        timeout = config.get("timeout", 30)
        max_retries = config.get("max_retries", 3)
        retry_delay = config.get("retry_delay", 2)
        rate_limit_delay = config.get("rate_limit_delay", 0)
        transform = config.get("transform")
        items_path = config.get("items_path")
        item_fields = config.get("item_fields")

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                raw_data = await self._http_get(base_url, headers, timeout)

                if rate_limit_delay > 0:
                    await asyncio.sleep(rate_limit_delay)

                if transform and callable(transform):
                    return transform(raw_data, source_id)

                return self._extract_items(
                    source_id, raw_data, items_path, item_fields,
                )
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    wait = retry_delay * (2 ** attempt)
                    logger.warning(
                        "API fetch failed for %s (attempt %d/%d): %s. "
                        "Retrying in %ds...",
                        source_id,
                        attempt + 1,
                        max_retries + 1,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"API fetch failed after {max_retries + 1} attempts for "
            f"'{source_id}': {last_error}"
        )

    async def _http_get(
        self, url: str, headers: dict[str, str], timeout: int,
    ) -> Any:
        """Perform async HTTP GET and return parsed JSON."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

    def _extract_items(
        self,
        source_id: str,
        raw_data: Any,
        items_path: str | None,
        item_fields: dict[str, str] | None,
    ) -> list[dict[str, str]]:
        """Extract items from raw JSON using paths.

        If items_path is provided, navigates the JSON structure.
        If item_fields is provided, maps output fields to JSON paths.
        Otherwise, wraps raw_data as a single item.
        """
        items_raw = raw_data

        if items_path and isinstance(raw_data, dict):
            for key in items_path.split("."):
                if isinstance(items_raw, dict):
                    items_raw = items_raw.get(key, [])
                else:
                    break

        if not isinstance(items_raw, list):
            items_raw = [items_raw]

        items = []
        for raw_item in items_raw:
            if item_fields and isinstance(raw_item, dict | int | str):
                item = self._map_fields(source_id, raw_item, item_fields)
            elif isinstance(raw_item, dict):
                item = self._normalize_dict(source_id, raw_item)
            else:
                item = self._normalize_value(source_id, raw_item)

            if item:
                items.append(item)

        return items

    def _map_fields(
        self,
        source_id: str,
        raw_item: Any,
        item_fields: dict[str, str],
    ) -> dict[str, str]:
        """Map output fields to JSON paths in raw_item."""
        mapped: dict[str, str] = {}
        for out_field, json_path in item_fields.items():
            value = raw_item
            for key in json_path.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            if value is not None:
                mapped[out_field] = str(value)

        mapped.setdefault("source_id", source_id)
        content_hash = hashlib.sha256(
            f"{source_id}:{mapped.get('url', mapped.get('id', ''))}".encode()
        ).hexdigest()[:16]
        mapped["content_hash"] = content_hash
        mapped["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return mapped

    def _normalize_dict(
        self, source_id: str, raw_item: dict,
    ) -> dict[str, str]:
        """Normalize a dict item with standard fields."""
        url = raw_item.get("url", raw_item.get("link", ""))
        title = raw_item.get("title", raw_item.get("name", "No title"))

        if not url and not title:
            return {}

        content_hash = hashlib.sha256(
            f"{source_id}:{url}".encode()
        ).hexdigest()[:16]

        return {
            "title": str(title).strip(),
            "url": str(url).strip() if url else "",
            "published": str(raw_item.get("published", raw_item.get("created_at", ""))),
            "summary": str(raw_item.get("description", raw_item.get("summary", "")))[:500],
            "source_id": source_id,
            "content_hash": content_hash,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _normalize_value(
        self, source_id: str, raw_value: Any,
    ) -> dict[str, str]:
        """Normalize a scalar value (e.g., an integer ID)."""
        return {
            "title": str(raw_value),
            "url": str(raw_value),
            "source_id": source_id,
            "content_hash": hashlib.sha256(
                f"{source_id}:{raw_value}".encode()
            ).hexdigest()[:16],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
