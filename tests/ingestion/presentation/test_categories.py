"""
Tests for Category API endpoints (Sprint 6.3B).

Validates REST endpoints for Category CRUD + lifecycle.
Uses DI override for CategoryService to test HTTP layer only.
No Application/Domain/Persistence layers are touched.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient

from ingestion.presentation.app import create_app
from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import get_category_service
from ingestion.application.dto.category_dto import CategoryDetailDTO, CategorySummaryDTO
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
    """Create a CategoryDetailDTO with sensible defaults."""
    defaults = dict(
        id="cat-001",
        name="Technology",
        slug="technology",
        is_active=True,
        parent_id=None,
    )
    defaults.update(overrides)
    return CategoryDetailDTO(**defaults)


def _make_summary_dto(**overrides):
    """Create a CategorySummaryDTO with sensible defaults."""
    defaults = dict(
        id="cat-001",
        name="Technology",
        slug="technology",
        is_active=True,
    )
    defaults.update(overrides)
    return CategorySummaryDTO(**defaults)


def _success_error(code, message="Error occurred"):
    """Create a failure Result with the given error code."""
    return Result.failure(Error(code=code, message=message))


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service():
    """Mock CategoryService returning success by default for all methods."""
    service = MagicMock()
    service.execute_create_category.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_find_category.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_update_category.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_activate_category.return_value = Result.success(
        _make_detail_dto(is_active=True)
    )
    service.execute_deactivate_category.return_value = Result.success(
        _make_detail_dto(is_active=False)
    )
    service.execute_list_categories.return_value = Result.success(
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
    """Fresh FastAPI app with mocked CategoryService dependency."""
    application = create_app(settings=_make_settings())
    application.dependency_overrides[get_category_service] = (
        lambda: mock_service
    )
    return application


@pytest.fixture
def client(app):
    """Async httpx client wired to the test app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/categories — Create Category
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateCategory:
    """POST /api/v1/categories endpoint tests."""

    @pytest.mark.anyio
    async def test_create_category_201(self, client):
        """Create category returns 201 with detail fields."""
        response = await client.post(
            "/api/v1/categories",
            json={
                "name": "Technology",
                "slug": "technology",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "cat-001"
        assert data["name"] == "Technology"
        assert data["slug"] == "technology"
        assert data["is_active"] is True
        assert data["parent_id"] is None

    @pytest.mark.anyio
    async def test_create_category_duplicate_409(self, app, mock_service):
        """Duplicate category slug returns 409 Conflict."""
        mock_service.execute_create_category.return_value = _success_error(
            IngestionErrorCode.DUPLICATE_NEWS_SOURCE,
            "Category slug 'technology' already exists",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/categories",
                json={
                    "name": "Technology",
                    "slug": "technology",
                },
            )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_category_validation_error(self, client):
        """Pydantic rejects empty name → 422."""
        response = await client.post(
            "/api/v1/categories",
            json={
                "name": "",
                "slug": "technology",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/categories/{category_id} — Get Category
# ══════════════════════════════════════════════════════════════════════════════


class TestGetCategory:
    """GET /api/v1/categories/{category_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_get_category_200(self, client):
        """Get category by ID returns 200 with detail."""
        response = await client.get("/api/v1/categories/cat-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "cat-001"
        assert data["name"] == "Technology"
        assert data["slug"] == "technology"
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_get_category_not_found_404(self, app, mock_service):
        """Non-existent category returns 404."""
        mock_service.execute_find_category.return_value = _success_error(
            IngestionErrorCode.CATEGORY_NOT_FOUND,
            "Category 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/categories/nonexistent")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/categories — List Categories
# ══════════════════════════════════════════════════════════════════════════════


class TestListCategories:
    """GET /api/v1/categories endpoint tests."""

    @pytest.mark.anyio
    async def test_list_categories_200(self, client):
        """List categories returns 200 with data and meta."""
        response = await client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "cat-001"
        assert data["meta"]["total"] == 1
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 50

    @pytest.mark.anyio
    async def test_list_categories_empty(self, app, mock_service):
        """List categories with no results returns empty data."""
        mock_service.execute_list_categories.return_value = Result.success(
            QueryResult(data=[], total=0, page=1, size=50)
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/categories/{category_id} — Update Category
# ══════════════════════════════════════════════════════════════════════════════


class TestUpdateCategory:
    """PUT /api/v1/categories/{category_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_update_category_200(self, client):
        """Update category returns 200 with detail."""
        response = await client.put(
            "/api/v1/categories/cat-001",
            json={"name": "Updated Tech"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "cat-001"

    @pytest.mark.anyio
    async def test_update_category_not_found_404(self, app, mock_service):
        """Update non-existent category returns 404."""
        mock_service.execute_update_category.return_value = _success_error(
            IngestionErrorCode.CATEGORY_NOT_FOUND,
            "Category 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.put(
                "/api/v1/categories/nonexistent",
                json={"name": "Updated Tech"},
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/categories/{category_id}/activate — Activate Category
# ══════════════════════════════════════════════════════════════════════════════


class TestActivateCategory:
    """POST /api/v1/categories/{category_id}/activate endpoint tests."""

    @pytest.mark.anyio
    async def test_activate_category_200(self, client):
        """Activate category returns 200 with is_active=True."""
        response = await client.post("/api/v1/categories/cat-001/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_activate_category_not_found_404(self, app, mock_service):
        """Activate non-existent category returns 404."""
        mock_service.execute_activate_category.return_value = _success_error(
            IngestionErrorCode.CATEGORY_NOT_FOUND,
            "Category 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/categories/nonexistent/activate"
            )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/categories/{category_id}/deactivate — Deactivate Category
# ══════════════════════════════════════════════════════════════════════════════


class TestDeactivateCategory:
    """POST /api/v1/categories/{category_id}/deactivate endpoint tests."""

    @pytest.mark.anyio
    async def test_deactivate_category_200(self, client):
        """Deactivate category returns 200 with is_active=False."""
        response = await client.post("/api/v1/categories/cat-001/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.anyio
    async def test_deactivate_category_not_found_404(self, app, mock_service):
        """Deactivate non-existent category returns 404."""
        mock_service.execute_deactivate_category.return_value = _success_error(
            IngestionErrorCode.CATEGORY_NOT_FOUND,
            "Category 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/categories/nonexistent/deactivate"
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
        mock_service.execute_find_category.return_value = _success_error(
            IngestionErrorCode.CATEGORY_NOT_FOUND,
            "Category 'cat-999' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/categories/cat-999")
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "CATEGORY_NOT_FOUND"


class TestOpenAPISchema:
    """OpenAPI schema validation tests."""

    @pytest.mark.anyio
    async def test_openapi_schema_categories_tag(self, client):
        """Category endpoints use the Categories tag in OpenAPI."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        categories_path = paths.get("/api/v1/categories", {})
        post_op = categories_path.get("post", {})
        assert "Categories" in post_op.get("tags", [])

    @pytest.mark.anyio
    async def test_openapi_schema_category_endpoints(self, client):
        """All category endpoints appear in OpenAPI schema."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        expected_endpoints = {
            "/api/v1/categories": {"get", "post"},
            "/api/v1/categories/{category_id}": {"get", "put"},
            "/api/v1/categories/{category_id}/activate": {"post"},
            "/api/v1/categories/{category_id}/deactivate": {"post"},
        }

        for path, methods in expected_endpoints.items():
            assert path in paths, f"Missing path: {path}"
            actual_methods = set(paths[path].keys()) - {"parameters"}
            assert (
                methods <= actual_methods
            ), f"Path {path}: expected methods {methods}, got {actual_methods}"
