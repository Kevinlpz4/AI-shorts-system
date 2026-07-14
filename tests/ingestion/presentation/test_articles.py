"""
Tests for Article API endpoints (Sprint 6.3B).

Validates REST endpoints for Article CRUD.
Uses DI override for ArticleService to test HTTP layer only.
No Application/Domain/Persistence layers are touched.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from httpx import ASGITransport, AsyncClient

from ingestion.presentation.app import create_app
from ingestion.presentation.config import Settings
from ingestion.presentation.dependencies import get_article_service
from ingestion.application.dto.article_dto import RawArticleDetailDTO, RawArticleSummaryDTO
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
    """Create a RawArticleDetailDTO with sensible defaults."""
    defaults = dict(
        id="art-001",
        feed_id="feed-001",
        external_id="ext-123",
        content_hash="a" * 64,
        title="Test Article",
        url="https://example.com/article/1",
        author="John",
        language="es",
    )
    defaults.update(overrides)
    return RawArticleDetailDTO(**defaults)


def _make_summary_dto(**overrides):
    """Create a RawArticleSummaryDTO with sensible defaults."""
    defaults = dict(
        id="art-001",
        feed_id="feed-001",
        title="Test Article",
        url="https://example.com/article/1",
        author="John",
        language="es",
    )
    defaults.update(overrides)
    return RawArticleSummaryDTO(**defaults)


def _success_error(code, message="Error occurred"):
    """Create a failure Result with the given error code."""
    return Result.failure(Error(code=code, message=message))


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_service():
    """Mock ArticleService returning success by default for all methods."""
    service = MagicMock()
    service.execute_create_article.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_find_article.return_value = Result.success(
        _make_detail_dto()
    )
    service.execute_list_articles.return_value = Result.success(
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
    """Fresh FastAPI app with mocked ArticleService dependency."""
    application = create_app(settings=_make_settings())
    application.dependency_overrides[get_article_service] = (
        lambda: mock_service
    )
    return application


@pytest.fixture
def client(app):
    """Async httpx client wired to the test app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/articles — Create Article
# ══════════════════════════════════════════════════════════════════════════════


class TestCreateArticle:
    """POST /api/v1/articles endpoint tests."""

    @pytest.mark.anyio
    async def test_create_article_201(self, client):
        """Create article returns 201 with full detail fields."""
        response = await client.post(
            "/api/v1/articles",
            json={
                "feed_id": "550e8400-e29b-41d4-a716-446655440000",
                "external_id": "ext-123",
                "content_hash": "a" * 64,
                "title": "Breaking News",
                "url": "https://example.com/article/1",
                "author": "John Doe",
                "language": "es",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "art-001"
        assert data["feed_id"] == "feed-001"
        assert data["title"] == "Test Article"
        assert data["url"] == "https://example.com/article/1"
        assert data["author"] == "John"
        assert data["language"] == "es"

    @pytest.mark.anyio
    async def test_create_article_feed_not_found_409(self, app, mock_service):
        """Article with non-existent feed returns 409 Conflict."""
        mock_service.execute_create_article.return_value = _success_error(
            IngestionErrorCode.DUPLICATE_ARTICLE,
            "Article already exists",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.post(
                "/api/v1/articles",
                json={
                    "feed_id": "550e8400-e29b-41d4-a716-446655440000",
                    "external_id": "ext-123",
                    "content_hash": "a" * 64,
                    "title": "Breaking News",
                    "url": "https://example.com/article/1",
                },
            )
        assert response.status_code == 409

    @pytest.mark.anyio
    async def test_create_article_validation_error(self, client):
        """Pydantic rejects empty feed_id → 422."""
        response = await client.post(
            "/api/v1/articles",
            json={
                "feed_id": "",
                "external_id": "ext-123",
                "content_hash": "a" * 64,
                "title": "Breaking News",
                "url": "https://example.com/article/1",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/articles/{article_id} — Get Article
# ══════════════════════════════════════════════════════════════════════════════


class TestGetArticle:
    """GET /api/v1/articles/{article_id} endpoint tests."""

    @pytest.mark.anyio
    async def test_get_article_200(self, client):
        """Get article by ID returns 200 with detail."""
        response = await client.get("/api/v1/articles/art-001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "art-001"
        assert data["title"] == "Test Article"
        assert data["content_hash"] == "a" * 64
        assert data["external_id"] == "ext-123"

    @pytest.mark.anyio
    async def test_get_article_not_found_404(self, app, mock_service):
        """Non-existent article returns 404."""
        mock_service.execute_find_article.return_value = _success_error(
            IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
            "Article 'nonexistent' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/articles/nonexistent")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/articles — List Articles
# ══════════════════════════════════════════════════════════════════════════════


class TestListArticles:
    """GET /api/v1/articles endpoint tests."""

    @pytest.mark.anyio
    async def test_list_articles_200(self, client):
        """List articles returns 200 with data and meta."""
        response = await client.get(
            "/api/v1/articles", params={"feed_id": "feed-001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "art-001"
        assert data["meta"]["total"] == 1
        assert data["meta"]["page"] == 1
        assert data["meta"]["page_size"] == 50

    @pytest.mark.anyio
    async def test_list_articles_empty(self, app, mock_service):
        """List articles with no results returns empty data."""
        mock_service.execute_list_articles.return_value = Result.success(
            QueryResult(data=[], total=0, page=1, size=50)
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get(
                "/api/v1/articles", params={"feed_id": "feed-001"}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Problem Details & OpenAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestProblemDetails:
    """RFC 9457 Problem Details format tests."""

    @pytest.mark.anyio
    async def test_problem_details_format(self, app, mock_service):
        """Error responses have RFC 9457 Problem Details fields."""
        mock_service.execute_find_article.return_value = _success_error(
            IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
            "Article 'art-999' not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/articles/art-999")
        assert response.status_code == 404
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404
        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "RAW_ARTICLE_NOT_FOUND"

    @pytest.mark.anyio
    async def test_error_content_type(self, app, mock_service):
        """Error response has application/problem+json content type."""
        mock_service.execute_find_article.return_value = _success_error(
            IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
            "Article not found",
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as c:
            response = await c.get("/api/v1/articles/nope")
        assert response.status_code == 404
        assert "application/problem+json" in response.headers[
            "content-type"
        ]


class TestOpenAPISchema:
    """OpenAPI schema validation tests."""

    @pytest.mark.anyio
    async def test_openapi_schema_articles_tag(self, client):
        """Article endpoints use the Articles tag in OpenAPI."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        articles_path = paths.get("/api/v1/articles", {})
        post_op = articles_path.get("post", {})
        assert "Articles" in post_op.get("tags", [])

    @pytest.mark.anyio
    async def test_openapi_schema_article_endpoints(self, client):
        """All article endpoints appear in OpenAPI schema."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        expected_endpoints = {
            "/api/v1/articles": {"get", "post"},
            "/api/v1/articles/{article_id}": {"get"},
        }

        for path, methods in expected_endpoints.items():
            assert path in paths, f"Missing path: {path}"
            actual_methods = set(paths[path].keys()) - {"parameters"}
            assert (
                methods <= actual_methods
            ), f"Path {path}: expected methods {methods}, got {actual_methods}"
