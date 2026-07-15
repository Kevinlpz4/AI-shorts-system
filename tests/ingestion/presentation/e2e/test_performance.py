"""
Performance Audit — Sprint 6.6.

Repeats baseline benchmark to validate CRUD p95 < 100ms threshold.

Measures:
- POST Source + GET Source + GET list
- POST Feed + GET Feed + GET list
- POST Article + GET Article + GET list

Uses real SQLite infrastructure through E2E fixtures.

Note: Runs with fewer iterations than the full performance suite
(10 vs 50) to keep E2E suite execution time reasonable for CI.
"""

from __future__ import annotations

import logging
import statistics
import time

import pytest

from httpx import ASGITransport, AsyncClient

logger = logging.getLogger(__name__)

ITERATIONS = 10
P95_THRESHOLD_MS = 100.0


def _calculate_p95(latencies_ms: list[float]) -> float:
    """Calculate the 95th percentile."""
    sorted_lat = sorted(latencies_ms)
    index = int(len(sorted_lat) * 0.95)
    index = min(index, len(sorted_lat) - 1)
    return sorted_lat[index]


class TestSourcePerformanceE2E:
    """Measure Source CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_source_crud_p95_under_threshold(self, e2e_app):
        """Source CRUD p95 < 100ms."""
        async with AsyncClient(
            transport=ASGITransport(app=e2e_app),
            base_url="http://testserver",
        ) as client:
            latencies: list[float] = []
            created_ids: list[str] = []

            for i in range(ITERATIONS):
                payload = {
                    "name": f"PerfE2E Source {i}",
                    "source_type": "RSS",
                    "source_url": f"https://pere2e-src-{i}.example.com/rss",
                }
                start = time.perf_counter()
                create_resp = await client.post(
                    "/api/v1/sources", json=payload
                )
                elapsed = (time.perf_counter() - start) * 1000

                assert create_resp.status_code == 201
                source_id = create_resp.json()["id"]
                created_ids.append(source_id)
                latencies.append(elapsed)

            # GET each
            for source_id in created_ids:
                start = time.perf_counter()
                get_resp = await client.get(f"/api/v1/sources/{source_id}")
                elapsed = (time.perf_counter() - start) * 1000
                assert get_resp.status_code == 200
                latencies.append(elapsed)

            # LIST once
            start = time.perf_counter()
            list_resp = await client.get("/api/v1/sources")
            elapsed = (time.perf_counter() - start) * 1000
            assert list_resp.status_code == 200
            latencies.append(elapsed)

            p95 = _calculate_p95(latencies)
            avg = statistics.mean(latencies)
            logger.info(
                "Source CRUD perf (E2E): p95=%.2fms avg=%.2fms (n=%d)",
                p95, avg, len(latencies),
            )

            assert p95 < P95_THRESHOLD_MS, (
                f"Source CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
            )


class TestFeedPerformanceE2E:
    """Measure Feed CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_feed_crud_p95_under_threshold(self, e2e_app):
        """Feed CRUD p95 < 100ms."""
        async with AsyncClient(
            transport=ASGITransport(app=e2e_app),
            base_url="http://testserver",
        ) as client:
            # Create source first
            src_resp = await client.post(
                "/api/v1/sources",
                json={
                    "name": "PerfE2E Feed Source",
                    "source_type": "RSS",
                    "source_url": "https://pere2e-feed-src.example.com/rss",
                },
            )
            assert src_resp.status_code == 201
            source_id = src_resp.json()["id"]

            latencies: list[float] = []
            created_ids: list[str] = []

            for i in range(ITERATIONS):
                payload = {
                    "source_id": source_id,
                    "url": f"https://pere2e-feed-{i}.example.com/rss",
                    "label": f"PerfE2E Feed {i}",
                    "language": "es",
                    "sync_mode": "PULL",
                }
                start = time.perf_counter()
                create_resp = await client.post(
                    "/api/v1/feeds", json=payload
                )
                elapsed = (time.perf_counter() - start) * 1000

                assert create_resp.status_code == 201
                feed_id = create_resp.json()["id"]
                created_ids.append(feed_id)
                latencies.append(elapsed)

            # GET each
            for feed_id in created_ids:
                start = time.perf_counter()
                get_resp = await client.get(f"/api/v1/feeds/{feed_id}")
                elapsed = (time.perf_counter() - start) * 1000
                assert get_resp.status_code == 200
                latencies.append(elapsed)

            # LIST once
            start = time.perf_counter()
            list_resp = await client.get(
                f"/api/v1/sources/{source_id}/feeds"
            )
            elapsed = (time.perf_counter() - start) * 1000
            assert list_resp.status_code == 200
            latencies.append(elapsed)

            p95 = _calculate_p95(latencies)
            avg = statistics.mean(latencies)
            logger.info(
                "Feed CRUD perf (E2E): p95=%.2fms avg=%.2fms (n=%d)",
                p95, avg, len(latencies),
            )

            assert p95 < P95_THRESHOLD_MS, (
                f"Feed CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
            )


class TestArticlePerformanceE2E:
    """Measure Article CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_article_crud_p95_under_threshold(self, e2e_app):
        """Article CRUD p95 < 100ms."""
        async with AsyncClient(
            transport=ASGITransport(app=e2e_app),
            base_url="http://testserver",
        ) as client:
            # Create source + feed
            src_resp = await client.post(
                "/api/v1/sources",
                json={
                    "name": "PerfE2E Article Source",
                    "source_type": "RSS",
                    "source_url": "https://pere2e-art-src.example.com/rss",
                },
            )
            assert src_resp.status_code == 201
            source_id = src_resp.json()["id"]

            feed_resp = await client.post(
                "/api/v1/feeds",
                json={
                    "source_id": source_id,
                    "url": "https://pere2e-art-feed.example.com/rss",
                    "label": "PerfE2E Article Feed",
                    "language": "es",
                },
            )
            assert feed_resp.status_code == 201
            feed_id = feed_resp.json()["id"]

            latencies: list[float] = []
            created_ids: list[str] = []

            for i in range(ITERATIONS):
                payload = {
                    "feed_id": feed_id,
                    "external_id": f"pere2e-ext-{i}",
                    "content_hash": f"{i:064d}",
                    "title": f"PerfE2E Article {i}",
                    "url": f"https://pere2e-art-{i}.example.com",
                }
                start = time.perf_counter()
                create_resp = await client.post(
                    "/api/v1/articles", json=payload
                )
                elapsed = (time.perf_counter() - start) * 1000

                assert create_resp.status_code == 201
                article_id = create_resp.json()["id"]
                created_ids.append(article_id)
                latencies.append(elapsed)

            # GET each
            for article_id in created_ids:
                start = time.perf_counter()
                get_resp = await client.get(
                    f"/api/v1/articles/{article_id}"
                )
                elapsed = (time.perf_counter() - start) * 1000
                assert get_resp.status_code == 200
                latencies.append(elapsed)

            # LIST once
            start = time.perf_counter()
            list_resp = await client.get(
                "/api/v1/articles",
                params={"feed_id": feed_id},
            )
            elapsed = (time.perf_counter() - start) * 1000
            assert list_resp.status_code == 200
            latencies.append(elapsed)

            p95 = _calculate_p95(latencies)
            avg = statistics.mean(latencies)
            logger.info(
                "Article CRUD perf (E2E): p95=%.2fms avg=%.2fms (n=%d)",
                p95, avg, len(latencies),
            )

            assert p95 < P95_THRESHOLD_MS, (
                f"Article CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
            )
