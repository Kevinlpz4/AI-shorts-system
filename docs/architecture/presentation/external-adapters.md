# Design: External Adapters

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Status**: Design-only — ports defined, adapters not implemented

---

## 1. Overview

External adapters are OUTBOUND adapters — they call external systems (RSS feeds, HTTP APIs, webhooks). They follow the Ports & Adapters pattern: the Application Layer defines ports (interfaces), and adapters implement them.

```
Application Layer (ports)
    │
    ▼
Infrastructure Layer (adapters)
    │
    ▼
External Systems
```

## 2. Collector Ports (Application Layer)

These ports already exist conceptually in the Application Layer. They define WHAT external data collection looks like, not HOW.

### RSS/Atom Collector Port

```python
# application/ports/collectors.py (future)
from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class CollectedItem:
    external_id: str
    title: str
    url: str
    author: str | None
    language: str | None
    published_at: datetime | None
    content_preview: str | None
    content_hash: str
    metadata: dict | None

class RSSCollector(Protocol):
    """Port for collecting items from RSS/Atom feeds."""

    def collect(self, feed_url: str, last_fetched: datetime | None = None) -> list[CollectedItem]:
        """Fetch and parse RSS/Atom feed. Returns new items."""
        ...
```

### HTTP API Collector Port

```python
class HTTPAPICollector(Protocol):
    """Port for collecting from REST/GraphQL APIs."""

    def collect(self, endpoint: str, auth: dict | None = None) -> list[CollectedItem]:
        """Fetch items from HTTP API endpoint."""
        ...
```

### Scraper Collector Port

```python
class ScraperCollector(Protocol):
    """Port for collecting via web scraping."""

    def collect(self, url: str, selectors: dict) -> list[CollectedItem]:
        """Scrape web page and extract items."""
        ...
```

## 3. Publisher Ports (Application Layer)

### Webhook Publisher Port

```python
@dataclass(frozen=True)
class WebhookPayload:
    event_type: str
    data: dict
    timestamp: datetime
    signature: str | None = None

class WebhookPublisher(Protocol):
    """Port for publishing events to external webhooks."""

    def publish(self, url: str, payload: WebhookPayload) -> bool:
        """POST payload to webhook URL. Returns success/failure."""
        ...
```

## 4. Adapter Implementations (Infrastructure Layer)

### RSS Adapter (Future)

```python
# infrastructure/adapters/rss_collector.py
import feedparser

class FeedParserRSSCollector:
    """RSS/Atom adapter using feedparser."""

    def collect(self, feed_url: str, last_fetched: datetime | None = None) -> list[CollectedItem]:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries:
            items.append(CollectedItem(
                external_id=entry.get("id", entry.get("link", "")),
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                author=entry.get("author"),
                language=feed.feed.get("language"),
                published_at=self._parse_date(entry.get("published")),
                content_preview=entry.get("summary"),
                content_hash=self._compute_hash(entry),
                metadata={"feed_title": feed.feed.get("title")},
            ))
        return items
```

### HTTP API Adapter (Future)

```python
# infrastructure/adapters/http_collector.py
import httpx

class HTTPClientCollector:
    """HTTP API adapter using httpx."""

    def collect(self, endpoint: str, auth: dict | None = None) -> list[CollectedItem]:
        response = httpx.get(endpoint, auth=auth)
        response.raise_for_status()
        # Parse response into CollectedItem list
        ...
```

### Scraper Adapter (Future)

```python
# infrastructure/adapters/scraper_collector.py
from selectolax.parser import HTMLParser

class SelectolaxScraperCollector:
    """Web scraping adapter using selectolax."""

    def collect(self, url: str, selectors: dict) -> list[CollectedItem]:
        response = httpx.get(url)
        tree = HTMLParser(response.text)
        # Extract items using CSS selectors
        ...
```

### Webhook Publisher Adapter (Future)

```python
# infrastructure/adapters/webhook_publisher.py
import httpx
import hmac
import hashlib

class HTTPWebhookPublisher:
    """Webhook adapter using httpx with HMAC signing."""

    def __init__(self, secret: str):
        self._secret = secret

    def publish(self, url: str, payload: WebhookPayload) -> bool:
        body = json.dumps(asdict(payload)).encode()
        signature = hmac.new(self._secret.encode(), body, hashlib.sha256).hexdigest()
        response = httpx.post(url, content=body, headers={"X-Signature": signature})
        return response.status_code < 400
```

## 5. Adapter Configuration

```python
# infrastructure/adapters/config.py
@dataclass(frozen=True)
class CollectorConfig:
    timeout_seconds: int = 30
    max_retries: int = 3
    user_agent: str = "AI-Shorts-System/1.0"
    verify_ssl: bool = True

@dataclass(frozen=True)
class WebhookConfig:
    secret: str = ""
    timeout_seconds: int = 10
    max_retries: int = 3
```

## 6. Dependency Rule Compliance

```
Presentation Layer → Application Layer (ports)
                          ↑
Infrastructure Layer → Application Layer (ports, implements)

Infrastructure adapters depend on APPLICATION PORTS, not Domain.
Domain has NO knowledge of adapters.
```

## 7. What's Implemented in Epic 6

NOTHING. This document is DESIGN ONLY. The ports are defined for future implementation. Epic 6 focuses on the Presentation Layer (HTTP adapter for humans/machines). External adapters (RSS, webhooks) are future epics.

---

*See also: `background-jobs.md`, `presentation-design.md`*
