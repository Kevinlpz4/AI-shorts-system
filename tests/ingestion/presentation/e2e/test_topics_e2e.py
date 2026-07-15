"""
E2E tests for Topic lifecycle — real infrastructure, no mocks.

Tests the full stack: HTTP → Router → Pydantic → Service → UoW → SQLite.

Scenarios:
- Create, duplicate detection, activate, deactivate, update, list
"""

from __future__ import annotations

import pytest


class TestTopicCreateE2E:
    """POST /api/v1/topics — Create Topic (E2E)."""

    @pytest.mark.anyio
    async def test_create_topic_201(self, e2e_client):
        """Create topic returns 201 with all fields."""
        response = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic Create"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "E2E Topic Create"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_topic_duplicate_422(self, e2e_client):
        """Duplicate topic name returns 422 (COMMAND_INVALID)."""
        name = "E2E Topic Duplicate"
        await e2e_client.post(
            "/api/v1/topics",
            json={"name": name},
        )
        response = await e2e_client.post(
            "/api/v1/topics",
            json={"name": name},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "COMMAND_INVALID"
        data = response.json()
        assert "error_code" in data

    @pytest.mark.anyio
    async def test_create_topic_empty_name_422(self, e2e_client):
        """Empty topic name returns 422."""
        response = await e2e_client.post(
            "/api/v1/topics",
            json={"name": ""},
        )
        assert response.status_code == 422


class TestTopicGetE2E:
    """GET /api/v1/topics/{topic_id} — Get Topic (E2E)."""

    @pytest.mark.anyio
    async def test_get_topic_by_list_200(self, e2e_client):
        """Find topic via list and name match."""
        await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic Get"},
        )
        response = await e2e_client.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        names = [t["name"] for t in data["data"]]
        assert "E2E Topic Get" in names


class TestTopicListE2E:
    """GET /api/v1/topics — List Topics (E2E)."""

    @pytest.mark.anyio
    async def test_list_topics_200(self, e2e_client):
        """List topics returns 200 with paginated results."""
        await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic List"},
        )

        response = await e2e_client.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        names = [t["name"] for t in data["data"]]
        assert "E2E Topic List" in names


class TestTopicUpdateE2E:
    """PUT /api/v1/topics/{topic_id} — Update Topic (E2E)."""

    @pytest.mark.anyio
    async def test_update_topic_200(self, e2e_client):
        """Update topic returns 200 with updated name."""
        create_resp = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic Before"},
        )
        topic_id = create_resp.json()["id"]

        response = await e2e_client.put(
            f"/api/v1/topics/{topic_id}",
            json={"name": "E2E Topic Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "E2E Topic Updated"

    @pytest.mark.anyio
    async def test_update_topic_not_found_404(self, e2e_client):
        """Update non-existent topic returns 404."""
        response = await e2e_client.put(
            "/api/v1/topics/00000000-0000-0000-0000-000000000000",
            json={"name": "Nope"},
        )
        assert response.status_code == 404


class TestTopicActivateE2E:
    """POST /api/v1/topics/{topic_id}/activate — Activate (E2E)."""

    @pytest.mark.anyio
    async def test_activate_topic_200(self, e2e_client):
        """Activate topic returns 200 with is_active=True."""
        create_resp = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic To Activate"},
        )
        topic_id = create_resp.json()["id"]

        # Deactivate first
        await e2e_client.post(
            f"/api/v1/topics/{topic_id}/deactivate",
            json={"reason": "Testing activate"},
        )

        response = await e2e_client.post(
            f"/api/v1/topics/{topic_id}/activate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


class TestTopicDeactivateE2E:
    """POST /api/v1/topics/{topic_id}/deactivate — Deactivate (E2E)."""

    @pytest.mark.anyio
    async def test_deactivate_topic_200(self, e2e_client):
        """Deactivate topic returns 200 with is_active=False."""
        create_resp = await e2e_client.post(
            "/api/v1/topics",
            json={"name": "E2E Topic To Deactivate"},
        )
        topic_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/topics/{topic_id}/deactivate",
            json={"reason": "Testing deactivate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
