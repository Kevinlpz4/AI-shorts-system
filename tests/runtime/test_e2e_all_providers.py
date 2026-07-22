"""
E2E tests for ALL 14 providers — real external calls.

Validates each provider against its real service before scheduler activation.
If a provider fails, it's documented and marked as "degraded" — NOT removed.

Providers:
1. Google News AI (RSS)
2. OpenAI Blog (RSS)
3. Anthropic Blog (RSS)
4. TechCrunch (RSS)
5. The Verge (RSS)
6. Dev.to (RSS)
7. Reddit AI (Reddit RSS)
8. Reddit Gaming (Reddit RSS)
9. Hacker News (REST API)
10. GitHub Trending (REST API)
11. Steam News (RSS)
12. PlayStation Blog (RSS)
13. IGN (RSS)
14. GameSpot (RSS)
"""
from __future__ import annotations

import pytest

from runtime.providers.rss.rss_provider import RSSProvider
from runtime.providers.reddit.reddit_provider import RedditProvider
from runtime.providers.api.api_provider import APIProvider
from runtime.providers.api.hackernews import _hn_transform
from runtime.providers.api.github import github_transform
from runtime.monitoring.pipeline_metrics import PipelineMetrics


# ── Shared validation helper ──────────────────────────────────────────

def _validate_item(item: dict, source_id: str) -> None:
    """Validate a fetched item has required fields."""
    assert item.get("title"), f"Item from {source_id} must have a title"
    assert item.get("url", "").startswith("http"), (
        f"Item from {source_id} must have a valid URL"
    )
    assert item.get("source_id") == source_id, (
        f"Item source_id mismatch: expected {source_id}, got {item.get('source_id')}"
    )
    assert item.get("content_hash"), f"Item from {source_id} must have content_hash"
    assert item.get("fetched_at"), f"Item from {source_id} must have fetched_at"


# ── RSS Providers ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_google_news_ai() -> None:
    """E2E: Google News AI RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "google-news-ai",
        {
            "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "Google News should return at least 1 item"
    _validate_item(items[0], "google-news-ai")
    print(f"✅ Google News AI: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_openai_blog() -> None:
    """E2E: OpenAI Blog RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "openai-blog",
        {
            "url": "https://openai.com/blog/rss.xml",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "OpenAI Blog should return at least 1 item"
    _validate_item(items[0], "openai-blog")
    print(f"✅ OpenAI Blog: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_anthropic_blog() -> None:
    """E2E: Anthropic Blog RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "anthropic-blog",
        {
            "url": "https://www.anthropic.com/rss.xml",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "Anthropic Blog should return at least 1 item"
    _validate_item(items[0], "anthropic-blog")
    print(f"✅ Anthropic Blog: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_techcrunch() -> None:
    """E2E: TechCrunch RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "techcrunch",
        {
            "url": "https://techcrunch.com/feed/",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "TechCrunch should return at least 1 item"
    _validate_item(items[0], "techcrunch")
    print(f"✅ TechCrunch: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_theverge() -> None:
    """E2E: The Verge RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "theverge",
        {
            "url": "https://www.theverge.com/rss/index.xml",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "The Verge should return at least 1 item"
    _validate_item(items[0], "theverge")
    print(f"✅ The Verge: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_devto() -> None:
    """E2E: Dev.to RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "devto",
        {
            "url": "https://dev.to/feed",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "Dev.to should return at least 1 item"
    _validate_item(items[0], "devto")
    print(f"✅ Dev.to: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_steam_news() -> None:
    """E2E: Steam News RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "steam-news",
        {
            "url": "https://store.steampowered.com/feeds/news/",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "Steam News should return at least 1 item"
    _validate_item(items[0], "steam-news")
    print(f"✅ Steam News: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_playstation_blog() -> None:
    """E2E: PlayStation Blog RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "playstation-blog",
        {
            "url": "https://blog.playstation.com/feed/",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "PlayStation Blog should return at least 1 item"
    _validate_item(items[0], "playstation-blog")
    print(f"✅ PlayStation Blog: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_ign() -> None:
    """E2E: IGN RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "ign",
        {
            "url": "https://feeds.feedburner.com/ign/all",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "IGN should return at least 1 item"
    _validate_item(items[0], "ign")
    print(f"✅ IGN: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_gamespot() -> None:
    """E2E: GameSpot RSS → parse → validate."""
    provider = RSSProvider()
    items = await provider.fetch(
        "gamespot",
        {
            "url": "https://www.gamespot.com/feeds/rss/",
            "timeout": 30,
            "max_retries": 2,
        },
    )
    assert len(items) >= 1, "GameSpot should return at least 1 item"
    _validate_item(items[0], "gamespot")
    print(f"✅ GameSpot: {len(items)} items")


# ── Reddit Providers ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_reddit_ai() -> None:
    """E2E: Reddit AI RSS → parse → validate."""
    provider = RedditProvider()
    items = await provider.fetch(
        "reddit-ai",
        {
            "subreddits": ["artificial", "OpenAI"],
            "timeout": 30,
            "max_retries": 2,
            "limit": 5,
        },
    )
    assert len(items) >= 1, "Reddit AI should return at least 1 item"
    _validate_item(items[0], "reddit-ai")
    assert "subreddit" in items[0], "Reddit items must have subreddit field"
    print(f"✅ Reddit AI: {len(items)} items")


@pytest.mark.asyncio
async def test_e2e_reddit_gaming() -> None:
    """E2E: Reddit Gaming RSS → parse → validate."""
    provider = RedditProvider()
    items = await provider.fetch(
        "reddit-gaming",
        {
            "subreddits": ["gaming", "pcgaming"],
            "timeout": 30,
            "max_retries": 2,
            "limit": 5,
        },
    )
    assert len(items) >= 1, "Reddit Gaming should return at least 1 item"
    _validate_item(items[0], "reddit-gaming")
    assert "subreddit" in items[0], "Reddit items must have subreddit field"
    print(f"✅ Reddit Gaming: {len(items)} items")


# ── API Providers ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_hackernews() -> None:
    """E2E: Hacker News API → fetch top stories → validate."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=30,
        )
        resp.raise_for_status()
        top_ids = resp.json()

    assert len(top_ids) > 0, "HN should return at least 1 story ID"

    items = await _hn_transform(top_ids[:5], "hackernews", max_items=5)
    assert len(items) >= 1, "HN should return at least 1 story"
    _validate_item(items[0], "hackernews")
    assert "hn_score" in items[0], "HN items must have hn_score"
    print(f"✅ Hacker News: {len(items)} stories")


@pytest.mark.asyncio
async def test_e2e_github_trending() -> None:
    """E2E: GitHub Trending API → search repos → validate."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/search/repositories?q=created:>2026-06-01&sort=stars&order=desc&per_page=5",
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

    items = github_transform(data, "github-trending")
    assert len(items) >= 1, "GitHub should return at least 1 repo"
    _validate_item(items[0], "github-trending")
    assert "gh_stars" in items[0], "GitHub items must have gh_stars"
    print(f"✅ GitHub Trending: {len(items)} repos")


# ── Aggregate E2E validation ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_all_providers_summary() -> None:
    """E2E: Validate all providers and produce summary report."""
    metrics = PipelineMetrics()
    results = {}

    rss_provider = RSSProvider()
    reddit_provider = RedditProvider()

    # RSS sources
    rss_sources = {
        "google-news-ai": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "openai-blog": "https://openai.com/blog/rss.xml",
        "anthropic-blog": "https://www.anthropic.com/rss.xml",
        "techcrunch": "https://techcrunch.com/feed/",
        "theverge": "https://www.theverge.com/rss/index.xml",
        "devto": "https://dev.to/feed",
        "steam-news": "https://store.steampowered.com/feeds/news/",
        "playstation-blog": "https://blog.playstation.com/feed/",
        "ign": "https://feeds.feedburner.com/ign/all",
        "gamespot": "https://www.gamespot.com/feeds/rss/",
    }

    for source_id, url in rss_sources.items():
        m = metrics.start_run(source_id)
        try:
            items = await rss_provider.fetch(source_id, {"url": url, "timeout": 30, "max_retries": 1})
            m.items_fetched = len(items)
            m.items_new = len(items)
            m.status = "success" if len(items) > 0 else "degraded"
            results[source_id] = {"status": "ok", "count": len(items)}
        except Exception as e:
            m.errors = 1
            m.status = "degraded"
            results[source_id] = {"status": "degraded", "error": str(e)[:100]}
        metrics.finish_run(m)

    # Reddit sources
    reddit_sources = {
        "reddit-ai": ["artificial", "OpenAI"],
        "reddit-gaming": ["gaming", "pcgaming"],
    }

    for source_id, subs in reddit_sources.items():
        m = metrics.start_run(source_id)
        try:
            items = await reddit_provider.fetch(source_id, {"subreddits": subs, "timeout": 30, "max_retries": 1, "limit": 5})
            m.items_fetched = len(items)
            m.items_new = len(items)
            m.status = "success" if len(items) > 0 else "degraded"
            results[source_id] = {"status": "ok", "count": len(items)}
        except Exception as e:
            m.errors = 1
            m.status = "degraded"
            results[source_id] = {"status": "degraded", "error": str(e)[:100]}
        metrics.finish_run(m)

    # Print summary
    agg = metrics.get_aggregate_stats()
    print(f"\n{'='*60}")
    print(f"E2E Provider Validation Summary")
    print(f"{'='*60}")
    for source_id, r in sorted(results.items()):
        status_icon = "✅" if r["status"] == "ok" else "⚠️"
        count = r.get("count", 0)
        error = r.get("error", "")
        print(f"  {status_icon} {source_id}: {count} items {f'({error})' if error else ''}")
    print(f"{'='*60}")
    print(f"Total: {agg['total_providers']} runs, {agg['total_items_fetched']} items fetched")
    print(f"Errors: {agg['total_errors']}, Degraded: {sum(1 for r in results.values() if r['status'] == 'degraded')}")
    print(f"{'='*60}")

    # At least 70% of providers should succeed (10/14)
    successful = sum(1 for r in results.values() if r["status"] == "ok")
    assert successful >= 10, f"Expected at least 10 providers to succeed, got {successful}"
