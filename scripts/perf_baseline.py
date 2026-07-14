"""Performance baseline script for Sprint 6.4.

Measures p50/p95/p99 latency for Source, Feed, and Article CRUD operations
using the Presentation Layer with mocked services.

This measures the OVERHEAD of the Presentation Layer itself:
- Middleware stack (Recovery, Timing, CorrelationID, RequestID)
- Request routing
- Pydantic serialization/deserialization
- Structured logging
- Exception handling

Methodology:
- httpx AsyncClient with ASGITransport
- DI-overridden mocked services (Application/Domain/Persistence NOT exercised)
- 50 iterations per operation
- p50/p95/p99 percentile calculation
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

# Ensure src/ is on path
_src_path = str(Path(__file__).resolve().parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from httpx import ASGITransport, AsyncClient


async def measure_operation(client: AsyncClient, operation, iterations: int = 50) -> dict:
    """Measure operation latency over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        response = await operation()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    p50 = times[int(len(times) * 0.50)]
    p95 = times[int(len(times) * 0.95)]
    p99 = times[int(len(times) * 0.99)]
    return {"p50": p50, "p95": p95, "p99": p99, "min": times[0], "max": times[-1]}


def _make_source_detail_dto(**overrides):
    from ingestion.application.dto.source_dto import SourceDetailDTO
    defaults = dict(
        id="src-perf-001", name="Perf Source", source_type="RSS",
        source_url="https://example.com/rss", is_active=True,
        categories=("cat-001",), topics=("top-001",),
    )
    defaults.update(overrides)
    return SourceDetailDTO(**defaults)


def _make_source_summary_dto(**overrides):
    from ingestion.application.dto.source_dto import SourceSummaryDTO
    defaults = dict(
        id="src-perf-001", name="Perf Source", source_type="RSS",
        source_url="https://example.com/rss", is_active=True,
    )
    defaults.update(overrides)
    return SourceSummaryDTO(**defaults)


def _make_feed_detail_dto(**overrides):
    from ingestion.application.dto.feed_dto import FeedDetailDTO
    defaults = dict(
        id="feed-perf-001", source_id="src-perf-001",
        url="https://example.com/rss/feed", label="Perf Feed",
        language="es", is_active=True, sync_mode="PULL",
        sync_interval_minutes=30, sync_max_retries=3,
        categories=("cat-001",), topics=("top-001",), retry_count=0,
    )
    defaults.update(overrides)
    return FeedDetailDTO(**defaults)


def _make_feed_summary_dto(**overrides):
    from ingestion.application.dto.feed_dto import FeedSummaryDTO
    defaults = dict(
        id="feed-perf-001", source_id="src-perf-001",
        url="https://example.com/rss/feed", label="Perf Feed",
        language="es", is_active=True, retry_count=0,
    )
    defaults.update(overrides)
    return FeedSummaryDTO(**defaults)


def _make_article_detail_dto(**overrides):
    from ingestion.application.dto.article_dto import RawArticleDetailDTO
    defaults = dict(
        id="art-perf-001", feed_id="feed-perf-001", external_id="ext-001",
        content_hash="a" * 64, title="Perf Article",
        url="https://example.com/article/1", author="Perf", language="es",
    )
    defaults.update(overrides)
    return RawArticleDetailDTO(**defaults)


def _make_article_summary_dto(**overrides):
    from ingestion.application.dto.article_dto import RawArticleSummaryDTO
    defaults = dict(
        id="art-perf-001", feed_id="feed-perf-001", title="Perf Article",
        url="https://example.com/article/1", author="Perf", language="es",
    )
    defaults.update(overrides)
    return RawArticleSummaryDTO(**defaults)


def _success(value):
    from foundation.result.result import Result
    return Result.success(value)


async def main():
    from ingestion.presentation.app import create_app
    from ingestion.presentation.config import Settings
    from ingestion.presentation.dependencies import (
        get_source_service, get_feed_service, get_article_service,
    )
    from ingestion.application.common.query_result import QueryResult

    settings = Settings(
        ENVIRONMENT="testing",
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=False,
        CORS_ORIGINS=[],
        LOG_LEVEL="WARNING",
        LOG_FORMAT="text",
    )
    app = create_app(settings=settings)

    # ── Mock Source Service ──
    source_service = MagicMock()
    source_service.execute_register_source.return_value = _success(_make_source_detail_dto())
    source_service.execute_find_source.return_value = _success(_make_source_detail_dto())
    source_service.execute_update_source.return_value = _success(_make_source_detail_dto())
    source_service.execute_enable_source.return_value = _success(_make_source_detail_dto(is_active=True))
    source_service.execute_disable_source.return_value = _success(_make_source_detail_dto(is_active=False))
    source_service.execute_list_active_sources.return_value = _success(
        QueryResult(data=[_make_source_summary_dto()], total=1, page=1, size=20)
    )
    app.dependency_overrides[get_source_service] = lambda: source_service

    # ── Mock Feed Service ──
    feed_service = MagicMock()
    feed_service.execute_register_feed.return_value = _success(_make_feed_detail_dto())
    feed_service.execute_find_feed.return_value = _success(_make_feed_detail_dto())
    feed_service.execute_update_feed.return_value = _success(_make_feed_detail_dto())
    feed_service.execute_activate_feed.return_value = _success(_make_feed_detail_dto(is_active=True))
    feed_service.execute_pause_feed.return_value = _success(_make_feed_detail_dto(is_active=False))
    feed_service.execute_record_collection.return_value = _success(_make_feed_detail_dto())
    feed_service.execute_record_failure.return_value = _success(_make_feed_detail_dto())
    feed_service.execute_list_feeds.return_value = _success(
        QueryResult(data=[_make_feed_summary_dto()], total=1, page=1, size=50)
    )
    app.dependency_overrides[get_feed_service] = lambda: feed_service

    # ── Mock Article Service ──
    article_service = MagicMock()
    article_service.execute_create_article.return_value = _success(_make_article_detail_dto())
    article_service.execute_find_article.return_value = _success(_make_article_detail_dto())
    article_service.execute_list_articles.return_value = _success(
        QueryResult(data=[_make_article_summary_dto()], total=1, page=1, size=50)
    )
    app.dependency_overrides[get_article_service] = lambda: article_service

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")

    # Warm up
    for _ in range(10):
        await client.get("/health/live")

    print("=" * 80)
    print("PERFORMANCE BASELINE — Ingestion API (Presentation Layer)")
    print(f"Mocked services | 50 iterations per operation")
    print("=" * 80)
    print()

    # ── Source CRUD ──
    print("── Source CRUD ──")

    source_payload = {
        "name": "Perf Source", "source_type": "RSS",
        "source_url": "https://example.com/rss",
    }

    results = await measure_operation(client, lambda: client.post("/api/v1/sources", json=source_payload))
    print(f"  Create:          p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_source_create = results

    results = await measure_operation(client, lambda: client.get("/api/v1/sources/src-perf-001"))
    print(f"  Get by ID:       p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_source_get = results

    results = await measure_operation(client, lambda: client.get("/api/v1/sources"))
    print(f"  List (paginated):p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_source_list = results
    print()

    # ── Feed CRUD ──
    print("── Feed CRUD ──")

    feed_payload = {
        "source_id": "src-perf-001", "url": "https://example.com/rss/feed",
        "label": "Perf Feed", "language": "es", "sync_mode": "PULL",
        "sync_interval_minutes": 30,
    }

    results = await measure_operation(client, lambda: client.post("/api/v1/feeds", json=feed_payload))
    print(f"  Create:          p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_feed_create = results

    results = await measure_operation(client, lambda: client.get("/api/v1/feeds/feed-perf-001"))
    print(f"  Get by ID:       p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_feed_get = results

    results = await measure_operation(client, lambda: client.get("/api/v1/sources/src-perf-001/feeds"))
    print(f"  List (paginated):p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_feed_list = results
    print()

    # ── Article CRUD ──
    print("── Article CRUD ──")

    article_payload = {
        "feed_id": "feed-perf-001", "external_id": "ext-001",
        "content_hash": "a" * 64, "title": "Perf Article",
        "url": "https://example.com/article/1", "author": "Perf", "language": "es",
    }

    results = await measure_operation(client, lambda: client.post("/api/v1/articles", json=article_payload))
    print(f"  Create:          p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_article_create = results

    results = await measure_operation(client, lambda: client.get("/api/v1/articles/art-perf-001"))
    print(f"  Get by ID:       p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_article_get = results

    results = await measure_operation(client, lambda: client.get("/api/v1/articles?feed_id=feed-perf-001"))
    print(f"  List (by feed):  p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_article_list = results
    print()

    # ── Health Endpoints ──
    print("── Health Endpoints ──")

    results = await measure_operation(client, lambda: client.get("/health/live"))
    print(f"  /health/live:    p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_health_live = results

    # Mock the health check's session_factory
    from ingestion.presentation.dependencies import get_session_factory
    mock_sf = MagicMock()
    mock_session = MagicMock()
    mock_session.execute.return_value = None

    class _FakeSessionCtx:
        def __init__(self, s): self._s = s
        def __enter__(self): return self._s
        def __exit__(self, *a): return False

    mock_sf.return_value = _FakeSessionCtx(mock_session)
    app.dependency_overrides[get_session_factory] = lambda: mock_sf

    results = await measure_operation(client, lambda: client.get("/health/ready"))
    print(f"  /health/ready:   p50={results['p50']:.2f}ms  p95={results['p95']:.2f}ms  p99={results['p99']:.2f}ms")
    results_health_ready = results
    print()

    # ── Summary Table ──
    print("=" * 80)
    print(f"{'Operation':<25} {'p50 (ms)':<12} {'p95 (ms)':<12} {'p99 (ms)':<12} {'Target':<10} {'Status'}")
    print("-" * 80)

    all_results = [
        ("Source create", results_source_create),
        ("Source get by ID", results_source_get),
        ("Source list", results_source_list),
        ("Feed create", results_feed_create),
        ("Feed get by ID", results_feed_get),
        ("Feed list", results_feed_list),
        ("Article create", results_article_create),
        ("Article get by ID", results_article_get),
        ("Article list", results_article_list),
        ("Health /live", results_health_live),
        ("Health /ready", results_health_ready),
    ]

    for name, r in all_results:
        status = "PASS" if r["p95"] < 100 else "FAIL"
        print(f"{name:<25} {r['p50']:<12.2f} {r['p95']:<12.2f} {r['p99']:<12.2f} {'<100ms':<10} {status}")

    print("=" * 80)
    print()
    print("NOTES:")
    print("- Presentation Layer overhead only (middleware, routing, serialization)")
    print("- Application/Domain/Persistence layers mocked — not exercised")
    print("- SQLite InMemory (no network latency)")
    print("- Production latency will include Application + DB layers")


if __name__ == "__main__":
    asyncio.run(main())
