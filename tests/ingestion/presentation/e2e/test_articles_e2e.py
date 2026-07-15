"""
E2E tests for Article lifecycle — real infrastructure, no mocks.

Tests the full stack: HTTP → Router → Pydantic → Service → UoW → SQLite.

Scenarios:
- Create, duplicate detection (by external_id), list by feed, get by ID
"""

from __future__ import annotations

import pytest


@pytest.fixture
async def _e2e_source(e2e_client):
    """Create a source for article tests."""
    resp = await e2e_client.post(
        "/api/v1/sources",
        json={
            "name": "E2E Article Source",
            "source_type": "RSS",
            "source_url": "https://e2e-article-src.example.com/rss",
        },
    )
    return resp.json()


@pytest.fixture
async def _e2e_feed(e2e_client, _e2e_source):
    """Create a feed for article tests."""
    resp = await e2e_client.post(
        "/api/v1/feeds",
        json={
            "source_id": _e2e_source["id"],
            "url": "https://e2e-article-feed.example.com/rss",
            "label": "E2E Article Feed",
            "language": "en",
        },
    )
    return resp.json()


class TestArticleCreateE2E:
    """POST /api/v1/articles — Register Article (E2E)."""

    @pytest.mark.anyio
    async def test_create_article_201(self, e2e_client, _e2e_feed):
        """Create article returns 201 with all fields."""
        response = await e2e_client.post(
            "/api/v1/articles",
            json={
                "feed_id": _e2e_feed["id"],
                "external_id": "e2e-art-001",
                "content_hash": "a" * 64,
                "title": "E2E Article Create",
                "url": "https://e2e-article-create.example.com/post",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "E2E Article Create"
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_article_duplicate_409(self, e2e_client, _e2e_feed):
        """Duplicate article external_id for same feed returns 409."""
        ext_id = "e2e-art-dup-001"
        url = "https://e2e-article-dup.example.com/post"
        await e2e_client.post(
            "/api/v1/articles",
            json={
                "feed_id": _e2e_feed["id"],
                "external_id": ext_id,
                "content_hash": "b" * 64,
                "title": "E2E Article Dup",
                "url": url,
            },
        )
        response = await e2e_client.post(
            "/api/v1/articles",
            json={
                "feed_id": _e2e_feed["id"],
                "external_id": ext_id,
                "content_hash": "c" * 64,
                "title": "E2E Article Dup 2",
                "url": url,
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "error_code" in data

    @pytest.mark.anyio
    async def test_create_article_missing_fields_422(self, e2e_client):
        """Article with missing required fields returns 422."""
        response = await e2e_client.post(
            "/api/v1/articles",
            json={},
        )
        assert response.status_code == 422


class TestArticleGetE2E:
    """GET /api/v1/articles/{article_id} — Get Article (E2E)."""

    @pytest.mark.anyio
    async def test_get_article_200(self, e2e_client, _e2e_feed):
        """Get existing article returns 200 with details."""
        create_resp = await e2e_client.post(
            "/api/v1/articles",
            json={
                "feed_id": _e2e_feed["id"],
                "external_id": "e2e-art-get-001",
                "content_hash": "d" * 64,
                "title": "E2E Article Get",
                "url": "https://e2e-article-get.example.com/post",
            },
        )
        article_id = create_resp.json()["id"]

        response = await e2e_client.get(f"/api/v1/articles/{article_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert data["title"] == "E2E Article Get"

    @pytest.mark.anyio
    async def test_get_article_not_found_404(self, e2e_client):
        """Non-existent article ID returns 404."""
        response = await e2e_client.get(
            "/api/v1/articles/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestArticleListE2E:
    """GET /api/v1/articles — List Articles (E2E)."""

    @pytest.mark.anyio
    async def test_list_articles_by_feed_200(self, e2e_client, _e2e_feed):
        """List articles for a feed returns 200 with results."""
        await e2e_client.post(
            "/api/v1/articles",
            json={
                "feed_id": _e2e_feed["id"],
                "external_id": "e2e-art-list-001",
                "content_hash": "e" * 64,
                "title": "E2E Article List",
                "url": "https://e2e-article-list.example.com/post",
            },
        )

        response = await e2e_client.get(
            "/api/v1/articles",
            params={"feed_id": _e2e_feed["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        titles = [a["title"] for a in data["data"]]
        assert "E2E Article List" in titles
