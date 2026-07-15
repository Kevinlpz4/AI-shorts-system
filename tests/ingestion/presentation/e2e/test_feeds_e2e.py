"""
E2E tests for Feed lifecycle — real infrastructure, no mocks.

Tests the full stack: HTTP → Router → Pydantic → Service → UoW → SQLite.

Scenarios:
- Create, duplicate detection, activate, deactivate
- Record collection, record failure, auto-pause
- Assign/remove category, assign/remove topic
- List feeds for source, get by ID
"""

from __future__ import annotations

import pytest


@pytest.fixture
async def _e2e_source(e2e_client):
    """Create a source to attach feeds to."""
    resp = await e2e_client.post(
        "/api/v1/sources",
        json={
            "name": "E2E Feed Source",
            "source_type": "RSS",
            "source_url": "https://e2e-feed-source.example.com/rss",
        },
    )
    return resp.json()


class TestFeedCreateE2E:
    """POST /api/v1/feeds — Register Feed (E2E)."""

    @pytest.mark.anyio
    async def test_create_feed_201(self, e2e_client, _e2e_source):
        """Create feed returns 201 with all fields."""
        response = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-create.example.com/rss",
                "label": "E2E Feed Create",
                "language": "es",
                "sync_mode": "PULL",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "E2E Feed Create"
        assert data["language"] == "es"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_feed_duplicate_409(self, e2e_client, _e2e_source):
        """Duplicate feed URL for same source returns 409."""
        url = "https://e2e-feed-dup.example.com/rss"
        await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": url,
                "label": "E2E Feed Dup",
                "language": "en",
            },
        )
        response = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": url,
                "label": "E2E Feed Dup 2",
                "language": "es",
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "error_code" in data

    @pytest.mark.anyio
    async def test_create_feed_invalid_url_422(self, e2e_client, _e2e_source):
        """Invalid feed URL returns 422."""
        response = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "not-a-url",
                "label": "E2E Bad URL Feed",
                "language": "es",
            },
        )
        assert response.status_code == 422


class TestFeedGetE2E:
    """GET /api/v1/feeds/{feed_id} — Get Feed (E2E)."""

    @pytest.mark.anyio
    async def test_get_feed_200(self, e2e_client, _e2e_source):
        """Get existing feed returns 200 with details."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-get.example.com/rss",
                "label": "E2E Feed Get",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        response = await e2e_client.get(f"/api/v1/feeds/{feed_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feed_id
        assert data["label"] == "E2E Feed Get"

    @pytest.mark.anyio
    async def test_get_feed_not_found_404(self, e2e_client):
        """Non-existent feed ID returns 404."""
        response = await e2e_client.get(
            "/api/v1/feeds/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestFeedListE2E:
    """GET /api/v1/sources/{source_id}/feeds — List Feeds (E2E)."""

    @pytest.mark.anyio
    async def test_list_feeds_for_source_200(self, e2e_client, _e2e_source):
        """List feeds for source returns 200 with feed list."""
        await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-list.example.com/rss",
                "label": "E2E Feed List",
                "language": "es",
            },
        )

        response = await e2e_client.get(
            f"/api/v1/sources/{_e2e_source['id']}/feeds"
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) > 0
        labels = [f["label"] for f in body["data"]]
        assert "E2E Feed List" in labels
        assert "meta" in body


class TestFeedActivateE2E:
    """POST /api/v1/feeds/{feed_id}/activate — Activate Feed (E2E).

    Note: Activate returns 204 No Content (no response body).
    """

    @pytest.mark.anyio
    async def test_activate_feed_204(self, e2e_client, _e2e_source):
        """Activate feed returns 204."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-activate.example.com/rss",
                "label": "E2E Feed Activate",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        # Pause first (feeds start active)
        await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/pause",
            json={"reason": "Testing activate"},
        )

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/activate"
        )
        assert response.status_code == 204


class TestFeedPauseE2E:
    """POST /api/v1/feeds/{feed_id}/pause — Pause Feed (E2E)."""

    @pytest.mark.anyio
    async def test_pause_feed_204(self, e2e_client, _e2e_source):
        """Pause feed returns 204."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-pause.example.com/rss",
                "label": "E2E Feed Pause",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/pause",
            json={"reason": "Testing pause"},
        )
        assert response.status_code == 204


class TestFeedCollectionE2E:
    """POST /api/v1/feeds/{feed_id}/collect — Record Collection (E2E)."""

    @pytest.mark.anyio
    async def test_record_collection_204(self, e2e_client, _e2e_source):
        """Record feed collection returns 204."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-collect.example.com/rss",
                "label": "E2E Feed Collect",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/collect",
            json={"count": 5},
        )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_record_collection_not_found_404(self, e2e_client):
        """Record collection for non-existent feed returns 404."""
        response = await e2e_client.post(
            "/api/v1/feeds/00000000-0000-0000-0000-000000000000/collect",
            json={"count": 5},
        )
        assert response.status_code == 404


class TestFeedFailureE2E:
    """POST /api/v1/feeds/{feed_id}/failure — Record Failure (E2E)."""

    @pytest.mark.anyio
    async def test_record_failure_204(self, e2e_client, _e2e_source):
        """Record feed failure returns 204."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-fail.example.com/rss",
                "label": "E2E Feed Fail",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/failure",
            json={"error": "Connection timeout"},
        )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_auto_pause_after_max_failures(self, e2e_client, _e2e_source):
        """Feed auto-pauses after reaching max consecutive failures."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-autopause.example.com/rss",
                "label": "E2E Feed AutoPause",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        # Record consecutive failures (domain default is 3)
        for _ in range(3):
            resp = await e2e_client.post(
                f"/api/v1/feeds/{feed_id}/failure",
                json={"error": "Simulated failure"},
            )
            assert resp.status_code == 204

        # Feed should now be inactive (auto-paused)
        get_resp = await e2e_client.get(f"/api/v1/feeds/{feed_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["is_active"] is False


class TestFeedUpdateE2E:
    """PUT /api/v1/feeds/{feed_id} — Update Feed (E2E)."""

    @pytest.mark.anyio
    async def test_update_feed_label_200(self, e2e_client, _e2e_source):
        """Update feed label returns 200."""
        create_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-update.example.com/rss",
                "label": "E2E Feed Before",
                "language": "es",
            },
        )
        feed_id = create_resp.json()["id"]

        response = await e2e_client.put(
            f"/api/v1/feeds/{feed_id}",
            json={"label": "E2E Feed Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "E2E Feed Updated"


class TestFeedAssignCategoryE2E:
    """POST /api/v1/feeds/{feed_id}/categories — Assign Category (E2E)."""

    @pytest.mark.anyio
    async def test_assign_category_to_feed_204(self, e2e_client, _e2e_source):
        """Assign category to feed returns 204."""
        feed_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-cat.example.com/rss",
                "label": "E2E Feed Cat",
                "language": "es",
            },
        )
        feed_id = feed_resp.json()["id"]

        cat_resp = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Cat For Feed", "slug": "e2e-cat-for-feed"},
        )
        category_id = cat_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/categories",
            json={"category_id": category_id},
        )
        assert response.status_code == 204


class TestFeedAssignTopicE2E:
    """POST /api/v1/feeds/{feed_id}/topics — Assign Topic (E2E)."""

    @pytest.mark.anyio
    async def test_assign_topic_to_feed_204(self, e2e_client, _e2e_source):
        """Assign topic to feed returns 204."""
        feed_resp = await e2e_client.post(
            "/api/v1/feeds",
            json={
                "source_id": _e2e_source["id"],
                "url": "https://e2e-feed-top.example.com/rss",
                "label": "E2E Feed Topic",
                "language": "es",
            },
        )
        feed_id = feed_resp.json()["id"]

        top_resp = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic For Feed"},
        )
        topic_id = top_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/feeds/{feed_id}/topics",
            json={"topic_id": topic_id},
        )
        assert response.status_code == 204
