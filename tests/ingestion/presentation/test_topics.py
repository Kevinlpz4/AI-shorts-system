"""
Tests for Topic API endpoints (Sprint 6.3B).

Validates REST endpoints for Topic CRUD + lifecycle.
Uses DI override for TopicService to test HTTP layer only.
No Application/Domain/Persistence layers are touched.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient

from ingestion.presentation.app import create_app
from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import get_topic_service
from ingestion.application.dto.topic_dto import TopicDetailDTO, TopicSummaryDTO
from ingestion.application.common.query_result import QueryResult
from ingestion.domain.exceptions.errors import IngestionErrorCode
from foundation.result.result import Error, Result


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _make_settings():
    """Create test Settings with in-memory SQLite."""
    return Settings(
        ENVIRONMENT="testing",
        DATABASE_URL="sqlite:///:memory:",
        CORS_ORIGINS=[],
        ALLOWED_HOSTS=["*"],
    )


def _make_detail_dto(**overrides):
    """Create a TopicDetailDTO with sensible defaults."""
    defaults = dict(
        id="top-001",
        name="AI Trends",
        description="AI stuff",
        is_active=True,
    )
    defaults.update(overrides)
    return TopicDetailDTO(**defaults)


def _make_summary_dto(**overrides):
    """Create a TopicSummaryDTO with sensible defaults."""
    defaults = dict(
        id="top-001",
        name="AI Trends",
        is_active=True,
    )
    defaults.update(overrides)
    return TopicSummaryDTO(**defaults)


def _success_error(code, message="Error occurred"):
    """Create a failure Result with the given error code."""
    return Result.failure(Error(code=code, message=message))


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service():
    """Mock TopicService returning success by default for all methods."""
    service = MagicMock()
    service.execute_create_topic.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_find_topic.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_update_topic.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_activate_topic.return_value = Result.success(
        _make_detail_dto(is_active=True)
    )
    service.execute_deactivate_topic.return_value = Result.success(
        _make_detail_dto(is_active=False)
    )
    service.execute_list_topics.return_value = Result.success(
        QueryResult(
            data=[_make_summary_dto()],
            total=1,
            page=1,
            size=50,
        )
    )
    return service


@pytest.fixture
def app(mock_service):
    """Fresh FastAPI app with mocked TopicService dependency."""
    application = create_app(settings=_make_settings())
    application.dependency_overrides[get_topic_service] = (
        lambda: mock_service
    )
    return application


@pytest.fixture
def client(app):
    """Async httpx client wired to the test app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/topics — Create Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateTopic:
    """POST /api/v1/topics endpoint tests."""

    @pytest.mark.anyio
    async def test_create_topic_201(self, client):
        """Create topic returns 201 with detail fields."""
        response = await client.post(
            "/api/v1/topics",
            json={
                "name": "AI Trends",
                "description": "Artificial intelligence trends",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "top-001"
        assert data["name"] == "AI Trends"
        assert data["description"] == "AI stuff"
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_create_topic_duplicate_409(self, app, mock_service):
        """Duplicate topic name returns 409 Conflict."""
        mock_service.execute_create_topic.return_value = _success_error(
            IngestionErrorCode.DUPLICATE_FEED_URL,
            "Topic name 'AI Trends' already exists",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/topics",
                json={
                    "name": "AI Trends",
                    "description": "AI stuff",
                },
            )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_topic_validation_error(self, client):
        """Pydantic rejects empty name → 422."""
        response = await client.post(
            "/api/v1/topics",
            json={
                "name": "",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/topics/{topic_id} — Get Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestGetTopic:
    """GET /api/v1/topics/{topic_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_get_topic_200(self, client):
        """Get topic by ID returns 200 with detail."""
        response = await client.get("/api/v1/topics/top-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "top-001"
        assert data["name"] == "AI Trends"
        assert data["description"] == "AI stuff"
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_get_topic_not_found_404(self, app, mock_service):
        """Non-existent topic returns 404."""
        mock_service.execute_find_topic.return_value = _success_error(
            IngestionErrorCode.TOPIC_NOT_FOUND,
            "Topic 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/topics/nonexistent")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/topics — List Topics
# ══════════════════════════════════════════════════════════════════════════════


class TestListTopics:
    """GET /api/v1/topics endpoint tests."""

    @pytest.mark.anyio
    async def test_list_topics_200(self, client):
        """List topics returns 200 with data and meta."""
        response = await client.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "top-001"
        assert data["meta"]["total"] == 1
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 50

    @pytest.mark.anyio
    async def test_list_topics_empty(self, app, mock_service):
        """List topics with no results returns empty data."""
        mock_service.execute_list_topics.return_value = Result.success(
            QueryResult(data=[], total=0, page=1, size=50)
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/topics/{topic_id} — Update Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateTopic:
    """PUT /api/v1/topics/{topic_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_update_topic_200(self, client):
        """Update topic returns 200 with detail."""
        response = await client.put(
            "/api/v1/topics/top-001",
            json={"name": "Updated AI"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "top-001"

    @pytest.mark.anyio
    async def test_update_topic_not_found_404(self, app, mock_service):
        """Update non-existent topic returns 404."""
        mock_service.execute_update_topic.return_value = _success_error(
            IngestionErrorCode.TOPIC_NOT_FOUND,
            "Topic 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.put(
                "/api/v1/topics/nonexistent",
                json={"name": "Updated AI"},
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/topics/{topic_id}/activate — Activate Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestActivateTopic:
    """POST /api/v1/topics/{topic_id}/activate endpoint tests."""

    @pytest.mark.anyio
    async def test_activate_topic_200(self, client):
        """Activate topic returns 200 with is_active=True."""
        response = await client.post("/api/v1/topics/top-001/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_activate_topic_not_found_404(self, app, mock_service):
        """Activate non-existent topic returns 404."""
        mock_service.execute_activate_topic.return_value = _success_error(
            IngestionErrorCode.TOPIC_NOT_FOUND,
            "Topic 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post("/api/v1/topics/nonexistent/activate")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/topics/{topic_id}/deactivate — Deactivate Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestDeactivateTopic:
    """POST /api/v1/topics/{topic_id}/deactivate endpoint tests."""

    @pytest.mark.anyio
    async def test_deactivate_topic_200(self, client):
        """Deactivate topic returns 200 with is_active=False."""
        response = await client.post("/api/v1/topics/top-001/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.anyio
    async def test_deactivate_topic_not_found_404(self, app, mock_service):
        """Deactivate non-existent topic returns 404."""
        mock_service.execute_deactivate_topic.return_value = _success_error(
            IngestionErrorCode.TOPIC_NOT_FOUND,
            "Topic 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/topics/nonexistent/deactivate"
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
        mock_service.execute_find_topic.return_value = _success_error(
            IngestionErrorCode.TOPIC_NOT_FOUND,
            "Topic 'top-999' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/topics/top-999")
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "TOPIC_NOT_FOUND"


class TestOpenAPISchema:
    """OpenAPI schema validation tests."""

    @pytest.mark.anyio
    async def test_openapi_schema_topics_tag(self, client):
        """Topic endpoints use the Topics tag in OpenAPI."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        topics_path = paths.get("/api/v1/topics", {})
        post_op = topics_path.get("post", {})
        assert "Topics" in post_op.get("tags", [])

    @pytest.mark.anyio
    async def test_openapi_schema_topic_endpoints(self, client):
        """All topic endpoints appear in OpenAPI schema."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        expected_endpoints = {
            "/api/v1/topics": {"get", "post"},
            "/api/v1/topics/{topic_id}": {"get", "put"},
            "/api/v1/topics/{topic_id}/activate": {"post"},
            "/api/v1/topics/{topic_id}/deactivate": {"post"},
        }

        for path, methods in expected_endpoints.items():
            assert path in paths, f"Missing path: {path}"
            actual_methods = set(paths[path].keys()) - {"parameters"}
            assert (
                methods <= actual_methods
            ), f"Path {path}: expected methods {methods}, got {actual_methods}"
