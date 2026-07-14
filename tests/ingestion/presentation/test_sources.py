"""
Tests for Source API endpoints (Sprint 6.2A).

Validates all 10 REST endpoints for NewsSource CRUD + lifecycle.
Uses DI override for SourceService and UoW to test HTTP layer only.
No Application/Domain/Persistence layers are touched.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient

from ingestion.presentation.app import create_app
from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import get_source_service, get_uow
from ingestion.application.dto.source_dto import SourceDetailDTO, SourceSummaryDTO
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
    """Create a SourceDetailDTO with sensible defaults."""
    defaults = dict(
        id="src-001",
        name="Test Source",
        source_type="RSS",
        source_url="https://example.com/rss",
        is_active=True,
        categories=("cat-001",),
        topics=("top-001",),
    )
    defaults.update(overrides)
    return SourceDetailDTO(**defaults)


def _make_summary_dto(**overrides):
    """Create a SourceSummaryDTO with sensible defaults."""
    defaults = dict(
        id="src-001",
        name="Test Source",
        source_type="RSS",
        source_url="https://example.com/rss",
        is_active=True,
    )
    defaults.update(overrides)
    return SourceSummaryDTO(**defaults)


def _make_mock_uow(find_result=None):
    """Create a mock SQLAlchemyUnitOfWork for DELETE endpoint tests."""
    mock_uow = MagicMock()
    mock_uow.__enter__ = MagicMock(return_value=mock_uow)
    mock_uow.__exit__ = MagicMock(return_value=False)
    mock_uow.commit = MagicMock()

    if find_result is None:
        mock_source = MagicMock()
        find_result = Result.success(mock_source)

    mock_uow.news_sources.find_by_id.return_value = find_result
    return mock_uow


def _success_error(code, message="Error occurred"):
    """Create a failure Result with the given IngestionErrorCode."""
    return Result.failure(Error(code=code, message=message))


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service():
    """Mock SourceService returning success by default for all methods."""
    service = MagicMock()
    service.execute_register_source.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_find_source.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_update_source.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_enable_source.return_value = Result.success(
        _make_detail_dto(is_active=True)
    )
    service.execute_disable_source.return_value = Result.success(
        _make_detail_dto(is_active=False)
    )
    service.execute_assign_category_to_source.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_assign_topic_to_source.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_list_active_sources.return_value = Result.success(
        QueryResult(
            data=[_make_summary_dto()],
            total=1,
            page=1,
            size=20,
        )
    )
    return service


@pytest.fixture
def app(mock_service):
    """Fresh FastAPI app with mocked SourceService dependency."""
    application = create_app(settings=_make_settings())
    application.dependency_overrides[get_source_service] = (
        lambda: mock_service
    )
    return application


@pytest.fixture
def client(app):
    """Async httpx client wired to the test app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sources — Register Source
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateSource:
    """POST /api/v1/sources endpoint tests."""

    @pytest.mark.anyio
    async def test_create_source_201(self, client):
        """Register source returns 201 with full detail fields."""
        response = await client.post(
            "/api/v1/sources",
            json={
                "name": "La Nación",
                "source_type": "RSS",
                "source_url": "https://www.lanacion.com.ar/rss",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "src-001"
        assert data["name"] == "Test Source"
        assert data["source_type"] == "RSS"
        assert data["source_url"] == "https://example.com/rss"
        assert data["is_active"] is True
        assert "categories" in data
        assert "topics" in data

    @pytest.mark.anyio
    async def test_create_source_duplicate_409(self, app, mock_service):
        """Duplicate source name returns 409 Conflict."""
        mock_service.execute_register_source.return_value = _success_error(
            IngestionErrorCode.DUPLICATE_NEWS_SOURCE,
            "Source name 'La Nación' already exists",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/sources",
                json={
                    "name": "La Nación",
                    "source_type": "RSS",
                    "source_url": "https://www.lanacion.com.ar/rss",
                },
            )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_source_invalid_url_422(self, app, mock_service):
        """Invalid source URL returns 422 Unprocessable Entity."""
        mock_service.execute_register_source.return_value = _success_error(
            IngestionErrorCode.INVALID_SOURCE_URL,
            "Invalid URL format",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/sources",
                json={
                    "name": "Bad URL Source",
                    "source_type": "RSS",
                    "source_url": "not-a-url",
                },
            )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_source_validation_error(self, client):
        """Pydantic rejects empty name → 422."""
        response = await client.post(
            "/api/v1/sources",
            json={
                "name": "",
                "source_type": "RSS",
                "source_url": "https://example.com/rss",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_create_source_invalid_source_type(self, client):
        """Pydantic rejects invalid source_type → 422."""
        response = await client.post(
            "/api/v1/sources",
            json={
                "name": "Test Source",
                "source_type": "INVALID",
                "source_url": "https://example.com/rss",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/sources — List Sources
# ══════════════════════════════════════════════════════════════════════════════


class TestListSources:
    """GET /api/v1/sources endpoint tests."""

    @pytest.mark.anyio
    async def test_list_sources_200(self, client):
        """List sources returns 200 with data and meta."""
        response = await client.get("/api/v1/sources")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "src-001"
        assert data["meta"]["total"] == 1
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 20


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/sources/{source_id} — Get Source
# ══════════════════════════════════════════════════════════════════════════════


class TestGetSource:
    """GET /api/v1/sources/{source_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_get_source_200(self, client):
        """Get source by ID returns 200 with detail."""
        response = await client.get("/api/v1/sources/src-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "src-001"
        assert data["name"] == "Test Source"
        assert data["categories"] == ["cat-001"]
        assert data["topics"] == ["top-001"]

    @pytest.mark.anyio
    async def test_get_source_not_found_404(self, app, mock_service):
        """Non-existent source returns 404."""
        mock_service.execute_find_source.return_value = _success_error(
            IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            "Source 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/sources/nonexistent")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/sources/{source_id} — Update Source
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateSource:
    """PUT /api/v1/sources/{source_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_update_source_200(self, client):
        """Update source returns 200 with detail."""
        response = await client.put(
            "/api/v1/sources/src-001",
            json={"name": "Updated Source"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "src-001"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sources/{source_id}/activate — Activate Source
# ══════════════════════════════════════════════════════════════════════════════


class TestActivateSource:
    """POST /api/v1/sources/{source_id}/activate endpoint tests."""

    @pytest.mark.anyio
    async def test_activate_source_200(self, client):
        """Activate source returns 200 with is_active=True."""
        response = await client.post("/api/v1/sources/src-001/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sources/{source_id}/deactivate — Deactivate Source
# ══════════════════════════════════════════════════════════════════════════════


class TestDeactivateSource:
    """POST /api/v1/sources/{source_id}/deactivate endpoint tests."""

    @pytest.mark.anyio
    async def test_deactivate_source_200(self, client):
        """Deactivate source returns 200 with is_active=False."""
        response = await client.post(
            "/api/v1/sources/src-001/deactivate",
            json={"reason": "No longer maintained"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.anyio
    async def test_deactivate_source_with_active_feeds_409(
        self, app, mock_service
    ):
        """Deactivate source with active feeds returns 409."""
        mock_service.execute_disable_source.return_value = _success_error(
            IngestionErrorCode.HAS_ACTIVE_FEEDS,
            "Cannot disable source with active feeds",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/sources/src-001/deactivate",
                json={"reason": "Trying to disable"},
            )
        assert response.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sources/{source_id}/categories — Assign Category
# ══════════════════════════════════════════════════════════════════════════════


class TestAssignCategory:
    """POST /api/v1/sources/{source_id}/categories endpoint tests."""

    @pytest.mark.anyio
    async def test_assign_category_204(self, client):
        """Assign category returns 204 No Content."""
        response = await client.post(
            "/api/v1/sources/src-001/categories",
            json={
                "category_id": "550e8400-e29b-41d4-a716-446655440000",
            },
        )
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/sources/{source_id}/categories/{category_id} — Remove Category
# ══════════════════════════════════════════════════════════════════════════════


class TestRemoveCategory:
    """DELETE /api/v1/sources/{source_id}/categories/{category_id} tests."""

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
                "/api/v1/sources/550e8400-e29b-41d4-a716-446655440000"
                "/categories/550e8400-e29b-41d4-a716-446655440001"
            )
        assert response.status_code == 204
        mock_uow.news_sources.find_by_id.assert_called_once()
        mock_uow.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_remove_category_not_found_404(self, app, mock_service):
        """Remove category from non-existent source returns 404."""
        mock_uow = _make_mock_uow(
            find_result=_success_error(
                IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                "Source not found",
            )
        )
        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.delete(
                "/api/v1/sources/550e8400-e29b-41d4-a716-446655440099"
                "/categories/550e8400-e29b-41d4-a716-446655440001"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/sources/{source_id}/topics — Assign Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestAssignTopic:
    """POST /api/v1/sources/{source_id}/topics endpoint tests."""

    @pytest.mark.anyio
    async def test_assign_topic_204(self, client):
        """Assign topic returns 204 No Content."""
        response = await client.post(
            "/api/v1/sources/src-001/topics",
            json={
                "topic_id": "550e8400-e29b-41d4-a716-446655440001",
            },
        )
        assert response.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/sources/{source_id}/topics/{topic_id} — Remove Topic
# ══════════════════════════════════════════════════════════════════════════════


class TestRemoveTopic:
    """DELETE /api/v1/sources/{source_id}/topics/{topic_id} tests."""

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
                "/api/v1/sources/550e8400-e29b-41d4-a716-446655440000"
                "/topics/550e8400-e29b-41d4-a716-446655440001"
            )
        assert response.status_code == 204
        mock_uow.news_sources.find_by_id.assert_called_once()
        mock_uow.commit.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# Problem Details & OpenAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestProblemDetails:
    """RFC 9457 Problem Details format tests."""

    @pytest.mark.anyio
    async def test_problem_details_format(self, app, mock_service):
        """Error responses have RFC 9457 Problem Details fields."""
        mock_service.execute_find_source.return_value = _success_error(
            IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            "Source 'src-999' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/sources/src-999")
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "NEWS_SOURCE_NOT_FOUND"

    @pytest.mark.anyio
    async def test_get_source_problem_detail_content_type(
        self, app, mock_service
    ):
        """Error response has application/problem+json content type."""
        mock_service.execute_find_source.return_value = _success_error(
            IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
            "Source not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/sources/nope")
        assert response.status_code == 404
        assert "application/problem+json" in response.headers[
            "content-type"
        ]


class TestOpenAPISchema:
    """OpenAPI schema validation tests."""

    @pytest.mark.anyio
    async def test_openapi_schema_sources_tag(self, client):
        """Source endpoints use the Sources tag in OpenAPI."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        # FastAPI applies router tags to operations, not top-level tags list
        paths = schema.get("paths", {})
        source_path = paths.get("/api/v1/sources", {})
        post_op = source_path.get("post", {})
        assert "Sources" in post_op.get("tags", [])

    @pytest.mark.anyio
    async def test_openapi_schema_source_endpoints(self, client):
        """All source endpoints appear in OpenAPI schema."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        expected_endpoints = {
            "/api/v1/sources": {"get", "post"},
            "/api/v1/sources/{source_id}": {"get", "put"},
            "/api/v1/sources/{source_id}/activate": {"post"},
            "/api/v1/sources/{source_id}/deactivate": {"post"},
            "/api/v1/sources/{source_id}/categories": {"post"},
            "/api/v1/sources/{source_id}/categories/{category_id}": {
                "delete"
            },
            "/api/v1/sources/{source_id}/topics": {"post"},
            "/api/v1/sources/{source_id}/topics/{topic_id}": {"delete"},
        }

        for path, methods in expected_endpoints.items():
            assert path in paths, f"Missing path: {path}"
            actual_methods = set(paths[path].keys()) - {"parameters"}
            assert (
                methods <= actual_methods
            ), f"Path {path}: expected methods {methods}, got {actual_methods}"
