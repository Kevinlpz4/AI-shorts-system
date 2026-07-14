"""
Performance Baseline Tests -- Sprint 6.4.

Measures CRUD operation performance against p95 < 100ms target.
Uses real SQLite InMemory database (not mocked).

Validates:
  - Source CRUD (create + get + list): p95 < 100ms, 50 iterations
  - Feed CRUD (create + get + list): p95 < 100ms, 50 iterations
  - Article CRUD (create + get + list): p95 < 100ms, 50 iterations
  - Health endpoint (/health/live + /health/ready): p95 < 100ms, 50 iterations

Uses a manually-built FastAPI app (bypassing create_app) to avoid
internal engine/session_factory conflicts with the perf engine.

IMPORTANT: Uses PerfUnitOfWork with idempotent __enter__ to handle the
double __enter__ pattern safely. The standard get_uow enters the UoW
context manager, then the service enters it again via ``with self._uow:``.
With StaticPool, this creates two sessions on the same connection. The
leaked first session causes transaction isolation issues (data written
by one session is invisible to the other). PerfUnitOfWork.__enter__
returns self when already entered, so both contexts share the same
session. PerfUnitOfWork.__exit__ only closes when the outermost context
exits (preventing premature session closure).
"""

from __future__ import annotations

import logging
import statistics
import time
from collections.abc import Callable
from typing import Self

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session, sessionmaker

from ingestion.presentation.config import Settings
from ingestion.infrastructure.persistence.base import PersistenceBase as Base
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

# Import models to register them in the metadata before create_all
import ingestion.infrastructure.persistence.models  # noqa: F401

logger = logging.getLogger(__name__)


# ============================================================================
# PerfUnitOfWork — idempotent __enter__ for StaticPool safety
# ============================================================================


class PerfUnitOfWork(SQLAlchemyUnitOfWork):
    """UoW subclass with idempotent __enter__/__exit__ for SQLite StaticPool.

    The standard UoW creates a new session on every __enter__ call. With
    StaticPool, two sessions on the same connection cause transaction
    isolation issues — data written by one session is invisible to the other.

    PerfUnitOfWork prevents this by:
    - __enter__: returning self if already entered (no new session)
    - __exit__: only closing when the outermost context exits

    This is TEST-ONLY infrastructure. Production UoW does not need this
    because PostgreSQL connection pools give each session its own connection.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        event_publisher=None,
    ) -> None:
        super().__init__(session_factory, event_publisher)
        self._entered_count = 0

    def __enter__(self) -> Self:
        """Idempotent — only creates session on first call."""
        self._entered_count += 1
        if self._session is None:
            super().__enter__()
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Only close when the outermost context exits."""
        self._entered_count -= 1
        if self._entered_count <= 0:
            super().__exit__(exc_type, exc_val, exc_tb)
            self._entered_count = 0

# -- Constants --

ITERATIONS = 50
P95_THRESHOLD_MS = 100.0


# -- Test-specific fixtures (isolated from shared conftest) --


@pytest.fixture
def perf_settings() -> Settings:
    """Settings for performance tests using SQLite in-memory."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=False,
        HOST="127.0.0.1",
        PORT=8000,
        DATABASE_URL="sqlite:///:memory:",
        CORS_ORIGINS=[],
        LOG_LEVEL="WARNING",
        LOG_FORMAT="text",
        SECRET_KEY="perf-test-key",
    )


@pytest.fixture
def perf_engine(perf_settings):
    """Create a real SQLAlchemy engine with tables created.

    Uses check_same_thread=False for SQLite in-memory with async.
    StaticPool ensures all sessions share the same connection.
    """
    from sqlalchemy.pool import StaticPool

    engine = sa_create_engine(
        perf_settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def perf_app(perf_settings, perf_engine):
    """Build FastAPI app manually for performance tests.

    Bypasses create_app() to avoid internal engine/session_factory
    conflicts. Overrides get_uow to avoid the double __enter__ pattern
    that causes SQLite StaticPool transaction isolation issues.
    """
    from ingestion.presentation.exceptions import register_exception_handlers
    from ingestion.presentation.health import router as health_router
    from ingestion.presentation.routers.sources import router as sources_router
    from ingestion.presentation.routers.feeds import router as feeds_router
    from ingestion.presentation.routers.articles import router as articles_router
    from ingestion.presentation.routers.categories import router as categories_router
    from ingestion.presentation.routers.topics import router as topics_router
    from ingestion.presentation.dependencies import (
        get_event_publisher,
        get_session_factory,
    )
    from ingestion.presentation.middleware import (
        CorrelationIDMiddleware,
        RecoveryMiddleware,
        RequestIDMiddleware,
        TimingMiddleware,
    )
    from ingestion.infrastructure.persistence.unit_of_work import (
        SQLAlchemyUnitOfWork,
    )

    _sf = sessionmaker(bind=perf_engine, expire_on_commit=False)

    # Override get_uow to use PerfUnitOfWork with idempotent __enter__.
    # The standard get_uow enters the UoW, then the service enters it again
    # via ``with self._uow:``. With StaticPool, this creates two sessions on
    # the same connection, causing transaction isolation issues.
    # PerfUnitOfWork.__enter__ returns self when already entered, so both
    # contexts share the same session. PerfUnitOfWork.__exit__ only closes
    # when the outermost context exits.
    def _perf_get_uow(
        session_factory: sessionmaker = Depends(get_session_factory),
        event_publisher=None,
    ):
        uow = PerfUnitOfWork(
            session_factory=session_factory,
            event_publisher=event_publisher,
        )
        with uow:
            yield uow

    application = FastAPI(
        title=f"AI Shorts System -- Ingestion API v{perf_settings.openapi_version}",
        version=perf_settings.openapi_version,
    )

    # Set state directly -- no lifespan, no internal engine
    application.state.settings = perf_settings
    application.state.engine = perf_engine
    application.state.session_factory = _sf

    # Middleware (order: last added = first executed)
    application.add_middleware(RecoveryMiddleware)
    application.add_middleware(TimingMiddleware)
    application.add_middleware(CorrelationIDMiddleware)
    application.add_middleware(RequestIDMiddleware)

    # Exception handlers
    register_exception_handlers(application)

    # Routers
    application.include_router(health_router)
    application.include_router(sources_router, prefix="/api/v1")
    application.include_router(feeds_router, prefix="/api/v1")
    application.include_router(articles_router, prefix="/api/v1")
    application.include_router(categories_router, prefix="/api/v1")
    application.include_router(topics_router, prefix="/api/v1")

    # DI overrides
    from ingestion.presentation.dependencies import get_uow
    application.dependency_overrides[get_session_factory] = lambda: _sf
    application.dependency_overrides[get_uow] = _perf_get_uow

    yield application


@pytest.fixture
async def perf_client(perf_app) -> AsyncClient:
    """Async client for performance tests."""
    transport = ASGITransport(app=perf_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ============================================================================
# Helpers
# ============================================================================


def _calculate_p95(latencies_ms: list[float]) -> float:
    """Calculate the 95th percentile from a list of latencies."""
    sorted_lat = sorted(latencies_ms)
    index = int(len(sorted_lat) * 0.95)
    index = min(index, len(sorted_lat) - 1)
    return sorted_lat[index]


# ============================================================================
# Source CRUD Performance
# ============================================================================


class TestSourcePerformance:
    """Measure Source CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_source_crud_p95_under_threshold(self, perf_client):
        """Source CRUD operations should complete within p95 < 100ms."""
        latencies: list[float] = []
        created_ids: list[str] = []

        for i in range(ITERATIONS):
            payload = {
                "name": f"Perf Source {i}",
                "source_type": "RSS",
                "source_url": f"https://perf-test-{i}.example.com/rss",
            }
            start = time.perf_counter()
            create_resp = await perf_client.post("/api/v1/sources", json=payload)
            elapsed = (time.perf_counter() - start) * 1000

            assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
            source_id = create_resp.json()["id"]
            created_ids.append(source_id)
            latencies.append(elapsed)

        # GET for each created source
        for source_id in created_ids:
            start = time.perf_counter()
            get_resp = await perf_client.get(f"/api/v1/sources/{source_id}")
            elapsed = (time.perf_counter() - start) * 1000
            assert get_resp.status_code == 200
            latencies.append(elapsed)

        # LIST (once, after all creates)
        start = time.perf_counter()
        list_resp = await perf_client.get("/api/v1/sources")
        elapsed = (time.perf_counter() - start) * 1000
        assert list_resp.status_code == 200
        latencies.append(elapsed)

        p95 = _calculate_p95(latencies)
        avg = statistics.mean(latencies)

        logger.info(
            "Source CRUD perf: p95=%.2fms avg=%.2fms (n=%d)",
            p95, avg, len(latencies),
        )

        assert p95 < P95_THRESHOLD_MS, (
            f"Source CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
        )


# ============================================================================
# Feed CRUD Performance
# ============================================================================


class TestFeedPerformance:
    """Measure Feed CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_feed_crud_p95_under_threshold(self, perf_client):
        """Feed CRUD operations should complete within p95 < 100ms."""
        # First create a source to attach feeds to
        source_payload = {
            "name": "Perf Feed Source",
            "source_type": "API",
            "source_url": "https://perf-feed-source.example.com",
        }
        source_resp = await perf_client.post("/api/v1/sources", json=source_payload)
        assert source_resp.status_code == 201, f"Source create failed: {source_resp.text}"
        source_id = source_resp.json()["id"]

        latencies: list[float] = []
        created_ids: list[str] = []

        for i in range(ITERATIONS):
            payload = {
                "source_id": source_id,
                "url": f"https://perf-feed-{i}.example.com/rss",
                "label": f"Perf Feed {i}",
                "language": "es",
                "sync_mode": "PULL",
            }
            start = time.perf_counter()
            create_resp = await perf_client.post("/api/v1/feeds", json=payload)
            elapsed = (time.perf_counter() - start) * 1000

            assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
            feed_id = create_resp.json()["id"]
            created_ids.append(feed_id)
            latencies.append(elapsed)

        # GET for each created feed
        for feed_id in created_ids:
            start = time.perf_counter()
            get_resp = await perf_client.get(f"/api/v1/feeds/{feed_id}")
            elapsed = (time.perf_counter() - start) * 1000
            assert get_resp.status_code == 200
            latencies.append(elapsed)

        # LIST feeds for source
        start = time.perf_counter()
        list_resp = await perf_client.get(f"/api/v1/sources/{source_id}/feeds")
        elapsed = (time.perf_counter() - start) * 1000
        assert list_resp.status_code == 200
        latencies.append(elapsed)

        p95 = _calculate_p95(latencies)
        avg = statistics.mean(latencies)

        logger.info(
            "Feed CRUD perf: p95=%.2fms avg=%.2fms (n=%d)",
            p95, avg, len(latencies),
        )

        assert p95 < P95_THRESHOLD_MS, (
            f"Feed CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
        )


# ============================================================================
# Article CRUD Performance
# ============================================================================


class TestArticlePerformance:
    """Measure Article CRUD performance: create + get + list."""

    @pytest.mark.anyio
    async def test_article_crud_p95_under_threshold(self, perf_client):
        """Article CRUD operations should complete within p95 < 100ms."""
        # Create source + feed to attach articles to
        source_resp = await perf_client.post(
            "/api/v1/sources",
            json={
                "name": "Perf Article Source",
                "source_type": "RSS",
                "source_url": "https://perf-article-source.example.com",
            },
        )
        assert source_resp.status_code == 201
        source_id = source_resp.json()["id"]

        feed_resp = await perf_client.post(
            "/api/v1/feeds",
            json={
                "source_id": source_id,
                "url": "https://perf-article-feed.example.com/rss",
                "label": "Perf Article Feed",
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
                "external_id": f"perf-ext-{i}",
                "content_hash": f"{i:064d}",  # unique per iteration
                "title": f"Perf Article {i}",
                "url": f"https://perf-article-{i}.example.com",
            }
            start = time.perf_counter()
            create_resp = await perf_client.post("/api/v1/articles", json=payload)
            elapsed = (time.perf_counter() - start) * 1000

            assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
            article_id = create_resp.json()["id"]
            created_ids.append(article_id)
            latencies.append(elapsed)

        # GET for each created article
        for article_id in created_ids:
            start = time.perf_counter()
            get_resp = await perf_client.get(f"/api/v1/articles/{article_id}")
            elapsed = (time.perf_counter() - start) * 1000
            assert get_resp.status_code == 200
            latencies.append(elapsed)

        # LIST articles for feed
        start = time.perf_counter()
        list_resp = await perf_client.get(
            "/api/v1/articles", params={"feed_id": feed_id}
        )
        elapsed = (time.perf_counter() - start) * 1000
        assert list_resp.status_code == 200
        latencies.append(elapsed)

        p95 = _calculate_p95(latencies)
        avg = statistics.mean(latencies)

        logger.info(
            "Article CRUD perf: p95=%.2fms avg=%.2fms (n=%d)",
            p95, avg, len(latencies),
        )

        assert p95 < P95_THRESHOLD_MS, (
            f"Article CRUD p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
        )


# ============================================================================
# Health Endpoint Performance
# ============================================================================


class TestHealthPerformance:
    """Measure health endpoint performance: liveness + readiness probes."""

    @pytest.mark.anyio
    async def test_health_endpoint_p95_under_threshold(self, perf_client):
        """Health endpoints should complete within p95 < 100ms."""
        latencies: list[float] = []

        for _ in range(ITERATIONS):
            # Liveness
            start = time.perf_counter()
            live_resp = await perf_client.get("/health/live")
            elapsed = (time.perf_counter() - start) * 1000
            assert live_resp.status_code == 200
            latencies.append(elapsed)

            # Readiness
            start = time.perf_counter()
            ready_resp = await perf_client.get("/health/ready")
            elapsed = (time.perf_counter() - start) * 1000
            assert ready_resp.status_code == 200
            latencies.append(elapsed)

        p95 = _calculate_p95(latencies)
        avg = statistics.mean(latencies)

        logger.info(
            "Health perf: p95=%.2fms avg=%.2fms (n=%d)",
            p95, avg, len(latencies),
        )

        assert p95 < P95_THRESHOLD_MS, (
            f"Health endpoint p95={p95:.2f}ms exceeds {P95_THRESHOLD_MS}ms threshold"
        )
