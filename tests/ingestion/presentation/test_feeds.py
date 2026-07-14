"""
Tests for Feed API endpoints (Sprint 6.2B).

Validates all 12 REST endpoints for Feed CRUD + lifecycle + sync tracking.
Uses DI override for FeedService and UoW to test HTTP layer only.
No Application/Domain/Persistence layers are touched.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient

from ingestion.presentation.app import create_app
from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import get_feed_service, get_uow
from ingestion.application.dto.feed_dto import FeedDetailDTO, FeedSummaryDTO
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.exceptions.errors import IngestionErrorCode
from foundation.result.result import Error, Result


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

UUID_SRC = "550e8400-e29b-41d4-a716-446655440000"
UUID_FEED = "550e8400-e29b-41d4-a716-446655440001"
UUID_CAT = "550e8400-e29b-41d4-a716-446655440002"
UUID_TOPIC = "550e8400-e29b-41d4-a716-446655440003"


def _make_settings():
    """Create test Settings with in-memory SQLite."""
    return Settings(
        ENVIRONMENT="testing",
        DATABASE_URL="sqlite:///:memory:",
        CORS_ORIGINS=[],
    )


def _make_feed_detail_dto(**overrides):
    """Create a FeedDetailDTO with sensible defaults."""
    defaults = dict(
        id=UUID_FEED,
        source_id=UUID_SRC,
        url="https://example.com/rss/feed",
        label="Test Feed",
        language="es",
        is_active=True,
        sync_mode="PULL",
        sync_interval_minutes=30,
        sync_max_retries=3,
        categories=("cat-001",),
        topics=("top-001",),
        retry_count=0,
    )
    defaults.update(overrides)
    return FeedDetailDTO(**defaults)


def _make_feed_summary_dto(**overrides):
    """Create a FeedSummaryDTO with sensible defaults."""
    defaults = dict(
        id=UUID_FEED,
        source_id=UUID_SRC,
        url="https://example.com/rss/feed",
        label="Test Feed",
        language="es",
        is_active=True,
        retry_count=0,
    )
    defaults.update(overrides)
    return FeedSummaryDTO(**defaults)


def _make_mock_uow(find_result=None):
    """Create a mock SQLAlchemyUnitOfWork for DELETE endpoint tests."""
    mock_uow = MagicMock()
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)
    mock_uow.commit = MagicMock()

    if find_result is None:
        mock_feed = MagicMock()
        find_result = Result.success(mock_feed)

    mock_uow.feeds.find_by_id.return_value = find_result
    return mock_uow


def _success_error(code, message="Error occurred"):
    """Create a failure Result with the given IngestionErrorCode."""
    return Result.failure(Error(code=code, message=message))


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service():
    """Mock FeedService returning success by default for all methods."""
    service = MagicMock()
    service.execute_register_feed.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_find_feed.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_update_feed.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_activate_feed.return_value = Result.success(
        _make_feed_detail_dto(is_active=True)
    )
    service.execute_pause_feed.return_value = Result.success(
        _make_feed_detail_dto(is_active=False)
    )
    service.execute_record_collection.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_record_failure.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_assign_category_to_feed.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_assign_topic_to_feed.return_value = Result.success(
        _make_feed_detail_dto()
    )
    service.execute_list_feeds.return_value = Result.success(
        QueryResult(
            data=[_make_feed_summary_dto()],
            total=1,
            page=1,
            size=50,
        )
    )
    return service


@pytest.fixture
def app(mock_service):
    """Fresh FastAPI app with mocked FeedService dependency."""
    application = create_app(settings=_make_settings())
    application.dependency_overrides[get_feed_service] = (
        lambda: mock_service
    )
    return application


@pytest.fixture
def client(app):
    """Async httpx client wired to the test app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds — Register Feed
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateFeed:
    """POST /api/v1/feeds endpoint tests."""

    @pytest.mark.anyio
    async def test_create_feed_201(self, client):
        """Register feed returns 201 with full detail fields."""
        response = await client.post(
            "/api/v1/feeds",
            json={
                "source_id": UUID_SRC,
                "url": "https://www.lanacion.com.ar/rss/feed",
                "label": "La Nación RSS",
                "language": "es",
                "sync_mode": "PULL",
                "sync_interval_minutes": 30,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == UUID_FEED
        assert data["source_id"] == UUID_SRC
        assert data["label"] == "Test Feed"
        assert data["sync_mode"] == "PULL"
        assert data["is_active"] is True
        assert "categories" in data
        assert "topics" in data

    @pytest.mark.anyio
    async def test_create_feed_duplicate_409(self, app, mock_service):
        """Duplicate feed URL returns 409 Conflict."""
        mock_service.execute_register_feed.return_value = _success_error(
            IngestionErrorCode.DUPLICATE_FEED_URL,
            "Feed URL already exists",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/feeds",
                json={
                    "source_id": UUID_SRC,
                    "url": "https://example.com/rss",
                    "label": "Test",
                    "language": "es",
                },
            )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_feed_source_not_found_404(self, app, mock_service):
        """Non-existent source returns 404."""
        mock_service.execute_register_feed.return_value = _success_error(
            IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            "Source not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/feeds",
                json={
                    "source_id": UUID_SRC,
                    "url": "https://example.com/rss",
                    "label": "Test",
                    "language": "es",
                },
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_create_feed_validation_error(self, client):
        """Pydantic rejects empty label → 422."""
        response = await client.post(
            "/api/v1/feeds",
            json={
                "source_id": UUID_SRC,
                "url": "https://example.com/rss",
                "label": "",
                "language": "es",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_create_feed_invalid_language(self, client):
        """Pydantic rejects invalid language code → 422."""
        response = await client.post(
            "/api/v1/feeds",
            json={
                "source_id": UUID_SRC,
                "url": "https://example.com/rss",
                "label": "Test",
                "language": "spanish",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_feed_invalid_sync_mode(self, client):
        """Pydantic rejects invalid sync_mode → 422."""
        response = await client.post(
            "/api/v1/feeds",
            json={
                "source_id": UUID_SRC,
                "url": "https://example.com/rss",
                "label": "Test",
                "language": "es",
                "sync_mode": "INVALID",
            },
        )
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/feeds/{feed_id} — Get Feed
# ══════════════════════════════════════════════════════════════════════════════


class TestGetFeed:
    """GET /api/v1/feeds/{feed_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_get_feed_200(self, client):
        """Get feed by ID returns 200 with detail."""
        response = await client.get(f"/api/v1/feeds/{UUID_FEED}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == UUID_FEED
        assert data["source_id"] == UUID_SRC
        assert data["categories"] == ["cat-001"]
        assert data["topics"] == ["top-001"]

    @pytest.mark.anyio
    async def test_get_feed_not_found_404(self, app, mock_service):
        """Non-existent feed returns 404."""
        mock_service.execute_find_feed.return_value = _success_error(
            IngestionErrorCode.FEED_NOT_FOUND,
            "Feed not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get(
                "/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/sources/{source_id}/feeds — List Feeds
# ══════════════════════════════════════════════════════════════════════════════


class TestListFeeds:
    """GET /api/v1/sources/{source_id}/feeds endpoint tests."""

    @pytest.mark.anyio
    async def test_list_feeds_200(self, client):
        """List feeds returns 200 with data and meta."""
        response = await client.get(f"/api/v1/sources/{UUID_SRC}/feeds")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == UUID_FEED
        assert data["meta"]["total"] == 1

    @pytest.mark.anyio
    async def test_list_feeds_with_pagination(self, client):
        """List feeds respects query params."""
        response = await client.get(
            f"/api/v1/sources/{UUID_SRC}/feeds?page=2&size=10"
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_list_feeds_source_not_found(self, app, mock_service):
        """Non-existent source returns 404."""
        mock_service.execute_list_feeds.return_value = _success_error(
            IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            "Source not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get(
                "/api/v1/sources/550e8400-e29b-41d4-a716-446655440099/feeds"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/feeds/{feed_id} — Update Feed
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateFeed:
    """PUT /api/v1/feeds/{feed_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_update_feed_200(self, client):
        """Update feed returns 200 with detail."""
        response = await client.put(
            f"/api/v1/feeds/{UUID_FEED}",
            json={"label": "Updated Feed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == UUID_FEED

    @pytest.mark.anyio
    async def test_update_feed_not_found_404(self, app, mock_service):
        """Update non-existent feed returns 404."""
        mock_service.execute_update_feed.return_value = _success_error(
            IngestionErrorCode.FEED_NOT_FOUND,
            "Feed not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.put(
                "/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099",
                json={"label": "Updated"},
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/activate — Activate Feed
# ══════════════════════════════════════════════════════════════════════════════


class TestActivateFeed:
    """POST /api/v1/feeds/{feed_id}/activate endpoint tests."""

    @pytest.mark.anyio
    async def test_activate_feed_204(self, client):
        """Activate feed returns 204 No Content."""
        response = await client.post(f"/api/v1/feeds/{UUID_FEED}/activate")
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/pause — Pause Feed
# ══════════════════════════════════════════════════════════════════════════════


class TestPauseFeed:
    """POST /api/v1/feeds/{feed_id}/pause endpoint tests."""

    @pytest.mark.anyio
    async def test_pause_feed_204(self, client):
        """Pause feed returns 204 No Content."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/pause",
            json={"reason": "Manual pause"},
        )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_pause_feed_already_paused_409(self, app, mock_service):
        """Pause already-paused feed returns 409."""
        mock_service.execute_pause_feed.return_value = _success_error(
            IngestionErrorCode.FEED_ALREADY_PAUSED,
            "Feed is already paused",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                f"/api/v1/feeds/{UUID_FEED}/pause",
                json={"reason": "Trying again"},
            )
        assert response.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/collect — Record Collection
# ══════════════════════════════════════════════════════════════════════════════


class TestRecordCollection:
    """POST /api/v1/feeds/{feed_id}/collect endpoint tests."""

    @pytest.mark.anyio
    async def test_record_collection_204(self, client):
        """Record collection returns 204 No Content."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/collect",
            json={"count": 5},
        )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_record_collection_with_batch_id(self, client):
        """Record collection with batch_id returns 204."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/collect",
            json={"count": 10, "batch_id": UUID_CAT},
        )
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/failure — Record Failure
# ══════════════════════════════════════════════════════════════════════════════


class TestRecordFailure:
    """POST /api/v1/feeds/{feed_id}/failure endpoint tests."""

    @pytest.mark.anyio
    async def test_record_failure_204(self, client):
        """Record failure returns 204 No Content."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/failure",
            json={"error": "Connection timeout"},
        )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_record_failure_max_retries_409(
        self, app, mock_service
    ):
        """Failure when max retries exceeded returns 409."""
        mock_service.execute_record_failure.return_value = _success_error(
            IngestionErrorCode.FEED_MAX_RETRIES_EXCEEDED,
            "Max retries exceeded",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                f"/api/v1/feeds/{UUID_FEED}/failure",
                json={"error": "Too many failures"},
            )
        assert response.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/categories — Assign Category
# ══════════════════════════════════════════════════════════════════════════════


class TestAssignCategory:
    """POST /api/v1/feeds/{feed_id}/categories endpoint tests."""

    @pytest.mark.anyio
    async def test_assign_category_204(self, client):
        """Assign category returns 204 No Content."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/categories",
            json={"category_id": UUID_CAT},
        )
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/feeds/{feed_id}/categories/{category_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestRemoveCategory:
    """DELETE /api/v1/feeds/{feed_id}/categories/{category_id} tests."""

    @pytest.mark.anyio
    async def test_remove_category_204(self, app, mock_service):
        """Remove category returns 204 No Content."""
        mock_uow = _make_mock_uow()
        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.delete(
                f"/api/v1/feeds/{UUID_FEED}/categories/{UUID_CAT}"
            )
        assert response.status_code == 204
        mock_uow.feeds.find_by_id.assert_called_once()
        mock_uow.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_remove_category_feed_not_found_404(
        self, app, mock_service
    ):
        """Remove category from non-existent feed returns 404."""
        mock_uow = _make_mock_uow(
            find_result=_success_error(
                IngestionErrorCode.FEED_NOT_FOUND,
                "Feed not found",
            )
        )
        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.delete(
                f"/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099"
                f"/categories/{UUID_CAT}"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/feeds/{feed_id}/topics — Assign Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestAssignTopic:
    """POST /api/v1/feeds/{feed_id}/topics endpoint tests."""

    @pytest.mark.anyio
    async def test_assign_topic_204(self, client):
        """Assign topic returns 204 No Content."""
        response = await client.post(
            f"/api/v1/feeds/{UUID_FEED}/topics",
            json={"topic_id": UUID_TOPIC},
        )
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/feeds/{feed_id}/topics/{topic_id}
# ══════════════════════════════════════════════════════════════════════════════


class TestRemoveTopic:
    """DELETE /api/v1/feeds/{feed_id}/topics/{topic_id} tests."""

    @pytest.mark.anyio
    async def test_remove_topic_204(self, app, mock_service):
        """Remove topic returns 204 No Content."""
        mock_uow = _make_mock_uow()
        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.delete(
                f"/api/v1/feeds/{UUID_FEED}/topics/{UUID_TOPIC}"
            )
        assert response.status_code == 204
        mock_uow.feeds.find_by_id.assert_called_once()
        mock_uow.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_remove_topic_feed_not_found_404(
        self, app, mock_service
    ):
        """Remove topic from non-existent feed returns 404."""
        mock_uow = _make_mock_uow(
            find_result=_success_error(
                IngestionErrorCode.FEED_NOT_FOUND,
                "Feed not found",
            )
        )
        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.delete(
                "/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099"
                f"/topics/{UUID_TOPIC}"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Problem Details & OpenAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestProblemDetails:
    """RFC 9457 Problem Details format tests."""

    @pytest.mark.anyio
    async def test_problem_details_format(self, app, mock_service):
        """Error responses have RFC 9457 Problem Details fields."""
        mock_service.execute_find_feed.return_value = _success_error(
            IngestionErrorCode.FEED_NOT_FOUND,
            "Feed not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get(
                "/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099"
            )
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "FEED_NOT_FOUND"

    @pytest.mark.anyio
    async def test_error_content_type(self, app, mock_service):
        """Error response has application/problem+json content type."""
        mock_service.execute_find_feed.return_value = _success_error(
            IngestionErrorCode.FEED_NOT_FOUND,
            "Feed not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get(
                "/api/v1/feeds/550e8400-e29b-41d4-a716-446655440099"
            )
        assert response.status_code == 404
        assert "application/problem+json" in response.headers[
            "content-type"
        ]


class TestOpenAPISchema:
    """OpenAPI schema validation tests."""

    @pytest.mark.anyio
    async def test_openapi_schema_feeds_tag(self, client):
        """Feed endpoints use the Feeds tag in OpenAPI."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        feed_path = paths.get("/api/v1/feeds", {})
        post_op = feed_path.get("post", {})
        assert "Feeds" in post_op.get("tags", [])

    @pytest.mark.anyio
    async def test_openapi_schema_feed_endpoints(self, client):
        """All feed endpoints appear in OpenAPI schema."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        expected_endpoints = {
            "/api/v1/feeds": {"post"},
            "/api/v1/feeds/{feed_id}": {"get", "put"},
            "/api/v1/feeds/{feed_id}/activate": {"post"},
            "/api/v1/feeds/{feed_id}/pause": {"post"},
            "/api/v1/feeds/{feed_id}/collect": {"post"},
            "/api/v1/feeds/{feed_id}/failure": {"post"},
            "/api/v1/feeds/{feed_id}/categories": {"post"},
            "/api/v1/feeds/{feed_id}/categories/{category_id}": {
                "delete"
            },
            "/api/v1/feeds/{feed_id}/topics": {"post"},
            "/api/v1/feeds/{feed_id}/topics/{topic_id}": {"delete"},
        }

        for path, methods in expected_endpoints.items():
            assert path in paths, f"Missing path: {path}"
            actual_methods = set(paths[path].keys()) - {"parameters"}
            assert (
                methods <= actual_methods
            ), f"Path {path}: expected {methods}, got {actual_methods}"

    @pytest.mark.anyio
    async def test_openapi_source_endpoints_still_present(self, client):
        """Source endpoints still present after adding feeds."""
        response = await client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/api/v1/sources" in paths
        assert "/api/v1/sources/{source_id}" in paths
