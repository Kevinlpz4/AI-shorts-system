"""
E2E tests for Source lifecycle — real infrastructure, no mocks.

Tests the full stack: HTTP → Router → Pydantic → Service → UoW → SQLite.

Scenarios:
- Create, duplicate detection, update, activate, deactivate
- Assign/remove category, assign/remove topic
- List, get by ID, not found
"""

from __future__ import annotations

import pytest


class TestSourceCreateE2E:
    """POST /api/v1/sources — Register Source (E2E)."""

    @pytest.mark.anyio
    async def test_create_source_201(self, e2e_client):
        """Create source returns 201 with all fields."""
        response = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source Create",
                "source_type": "RSS",
                "source_url": "https://e2e-create.example.com/rss",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "E2E Source Create"
        assert data["source_type"] == "RSS"
        assert data["source_url"] == "https://e2e-create.example.com/rss"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_source_duplicate_409(self, e2e_client):
        """Duplicate source name returns 409."""
        name = "E2E Source Duplicate"
        await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": name,
                "source_type": "RSS",
                "source_url": "https://e2e-dup.example.com/rss",
            },
        )
        response = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": name,
                "source_type": "API",
                "source_url": "https://e2e-dup-2.example.com/api",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "DUPLICATE_NEWS_SOURCE"

    @pytest.mark.anyio
    async def test_create_source_invalid_url_422(self, e2e_client):
        """Invalid source URL returns 422."""
        response = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Bad URL",
                "source_type": "RSS",
                "source_url": "not-a-valid-url",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_source_empty_name_422(self, e2e_client):
        """Empty name returns 422 via pydantic validation."""
        response = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "",
                "source_type": "RSS",
                "source_url": "https://e2e-empty.example.com/rss",
            },
        )
        assert response.status_code == 422


class TestSourceGetE2E:
    """GET /api/v1/sources/{source_id} — Get Source (E2E)."""

    @pytest.mark.anyio
    async def test_get_source_200(self, e2e_client):
        """Get existing source returns 200 with details."""
        create_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source Get",
                "source_type": "RSS",
                "source_url": "https://e2e-get.example.com/rss",
            },
        )
        source_id = create_resp.json()["id"]

        response = await e2e_client.get(f"/api/v1/sources/{source_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == source_id
        assert data["name"] == "E2E Source Get"

    @pytest.mark.anyio
    async def test_get_source_not_found_404(self, e2e_client):
        """Non-existent source ID (valid UUID) returns 404."""
        response = await e2e_client.get(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data


class TestSourceListE2E:
    """GET /api/v1/sources — List Sources (E2E)."""

    @pytest.mark.anyio
    async def test_list_sources_200(self, e2e_client):
        """List sources returns 200 with paginated results."""
        # Create a source
        await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source List",
                "source_type": "RSS",
                "source_url": "https://e2e-list.example.com/rss",
            },
        )

        response = await e2e_client.get("/api/v1/sources")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        # Should contain our source
        names = [s["name"] for s in data["data"]]
        assert "E2E Source List" in names


class TestSourceUpdateE2E:
    """PUT /api/v1/sources/{source_id} — Update Source (E2E)."""

    @pytest.mark.anyio
    async def test_update_source_200(self, e2e_client):
        """Update source returns 200 with updated fields."""
        create_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source Before Update",
                "source_type": "RSS",
                "source_url": "https://e2e-update.example.com/rss",
            },
        )
        source_id = create_resp.json()["id"]

        response = await e2e_client.put(
            f"/api/v1/sources/{source_id}",
            json={"name": "E2E Source Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == source_id
        assert data["name"] == "E2E Source Updated"

    @pytest.mark.anyio
    async def test_update_source_not_found_404(self, e2e_client):
        """Update non-existent source returns 404."""
        response = await e2e_client.put(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000",
            json={"name": "Nope"},
        )
        assert response.status_code == 404


class TestSourceActivateE2E:
    """POST /api/v1/sources/{source_id}/activate — Activate Source (E2E)."""

    @pytest.mark.anyio
    async def test_activate_source_200(self, e2e_client):
        """Activate source with active feed returns 200 with is_active=True.

        Note: AL-02 requires at least one active feed to activate.
        AL-01: Cannot deactivate source with active feeds.
        """
        # Create source
        src_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source To Activate",
                "source_type": "RSS",
                "source_url": "https://e2e-activate.example.com/rss",
            },
        )
        source_id = src_resp.json()["id"]

        # Create a feed (AL-02 requires active feed to enable)
        feed_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": source_id,
                "url": "https://e2e-activate-feed.example.com/rss",
                "label": "E2E Activate Feed",
                "language": "es",
            },
        )
        assert feed_resp.status_code == 201
        feed_id = feed_resp.json()["id"]

        # Pause feed first (AL-01: can't deactivate source with active feeds)
        feed_pause = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/pause",
            json={"reason": "Testing source reactivation"},
        )
        assert feed_pause.status_code == 204

        # Deactivate source
        deact = await e2e_client.post(
            f"/api/v1/sources/{source_id}/deactivate",
            json={"reason": "Testing activate"},
        )
        assert deact.status_code == 200

        # Re-activate feed (AL-02 requires active feed)
        await e2e_client.post(f"/api/v1/feeds/{feed_id}/activate")

        # Now activate source
        response = await e2e_client.post(
            f"/api/v1/sources/{source_id}/activate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_activate_source_no_feeds_409(self, e2e_client):
        """Activate source without active feeds returns 409 (AL-02)."""
        src_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source No Feed Activate",
                "source_type": "RSS",
                "source_url": "https://e2e-no-feed-activate.example.com/rss",
            },
        )
        source_id = src_resp.json()["id"]

        # Deactivate first
        await e2e_client.post(
            f"/api/v1/sources/{source_id}/deactivate",
            json={"reason": "Testing no-feed activate"},
        )

        response = await e2e_client.post(
            f"/api/v1/sources/{source_id}/activate"
        )
        assert response.status_code == 409


class TestSourceDeactivateE2E:
    """POST /api/v1/sources/{source_id}/deactivate — Deactivate Source (E2E)."""

    @pytest.mark.anyio
    async def test_deactivate_source_200(self, e2e_client):
        """Deactivate source returns 200 with is_active=False."""
        create_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source To Deactivate",
                "source_type": "RSS",
                "source_url": "https://e2e-deactivate.example.com/rss",
            },
        )
        source_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/sources/{source_id}/deactivate",
            json={"reason": "Testing deactivate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.anyio
    async def test_deactivate_source_not_found_404(self, e2e_client):
        """Deactivate non-existent source returns 404."""
        response = await e2e_client.post(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000/deactivate",
            json={"reason": "Nope"},
        )
        assert response.status_code == 404


class TestSourceAssignCategoryE2E:
    """POST /api/v1/sources/{source_id}/categories — Assign Category (E2E)."""

    @pytest.mark.anyio
    async def test_assign_category_to_source_204(self, e2e_client):
        """Assign category to source returns 204."""
        # Create source
        src_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source Cat Assign",
                "source_type": "RSS",
                "source_url": "https://e2e-cat-assign.example.com/rss",
            },
        )
        source_id = src_resp.json()["id"]

        # Create category (needs slug)
        cat_resp = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Cat For Source", "slug": "e2e-cat-for-source"},
        )
        category_id = cat_resp.json()["id"]

        # Assign
        response = await e2e_client.post(
            f"/api/v1/sources/{source_id}/categories",
            json={"category_id": category_id},
        )
        assert response.status_code == 204


class TestSourceAssignTopicE2E:
    """POST /api/v1/sources/{source_id}/topics — Assign Topic (E2E)."""

    @pytest.mark.anyio
    async def test_assign_topic_to_source_204(self, e2e_client):
        """Assign topic to source returns 204."""
        # Create source
        src_resp = await e2e_client.post(
            "/api/v1/sources",
            json={
                "name": "E2E Source Topic Assign",
                "source_type": "RSS",
                "source_url": "https://e2e-topic-assign.example.com/rss",
            },
        )
        source_id = src_resp.json()["id"]

        # Create topic
        top_resp = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic For Source"},
        )
        topic_id = top_resp.json()["id"]

        # Assign
        response = await e2e_client.post(
            f"/api/v1/sources/{source_id}/topics",
            json={"topic_id": topic_id},
        )
        assert response.status_code == 204
