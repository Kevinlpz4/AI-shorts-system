"""
E2E tests for Category lifecycle — real infrastructure, no mocks.

Tests the full stack: HTTP → Router → Pydantic → Service → UoW → SQLite.

Scenarios:
- Create, duplicate detection, activate, deactivate, update, list
"""

from __future__ import annotations

import pytest


class TestCategoryCreateE2E:
    """POST /api/v1/categories — Create Category (E2E)."""

    @pytest.mark.anyio
    async def test_create_category_201(self, e2e_client):
        """Create category returns 201 with all fields."""
        response = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category Create", "slug": "e2e-category-create"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "E2E Category Create"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.anyio
    async def test_create_category_duplicate_422(self, e2e_client):
        """Duplicate category slug returns 422 (COMMAND_INVALID)."""
        slug = "e2e-category-dup"
        await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category Duplicate", "slug": slug},
        )
        response = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category Duplicate 2", "slug": slug},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "COMMAND_INVALID"

    @pytest.mark.anyio
    async def test_create_category_empty_name_422(self, e2e_client):
        """Empty category name returns 422."""
        response = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "", "slug": ""},
        )
        assert response.status_code == 422


class TestCategoryGetE2E:
    """GET /api/v1/categories/{category_id} (via list + name match)."""

    @pytest.mark.anyio
    async def test_get_category_by_list_200(self, e2e_client):
        """Get category by listing and matching name."""
        await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category Get List", "slug": "e2e-category-get-list"},
        )
        response = await e2e_client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        names = [c["name"] for c in data["data"]]
        assert "E2E Category Get List" in names


class TestCategoryListE2E:
    """GET /api/v1/categories — List Categories (E2E)."""

    @pytest.mark.anyio
    async def test_list_categories_200(self, e2e_client):
        """List categories returns 200 with paginated results."""
        await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category List", "slug": "e2e-category-list"},
        )

        response = await e2e_client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        names = [c["name"] for c in data["data"]]
        assert "E2E Category List" in names


class TestCategoryUpdateE2E:
    """PUT /api/v1/categories/{category_id} — Update Category (E2E)."""

    @pytest.mark.anyio
    async def test_update_category_200(self, e2e_client):
        """Update category returns 200 with updated name."""
        create_resp = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category Before", "slug": "e2e-category-before"},
        )
        category_id = create_resp.json()["id"]

        response = await e2e_client.put(
            f"/api/v1/categories/{category_id}",
            json={"name": "E2E Category Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "E2E Category Updated"

    @pytest.mark.anyio
    async def test_update_category_not_found_404(self, e2e_client):
        """Update non-existent category returns 404."""
        response = await e2e_client.put(
            "/api/v1/categories/00000000-0000-0000-0000-000000000000",
            json={"name": "Nope"},
        )
        assert response.status_code == 404


class TestCategoryActivateE2E:
    """POST /api/v1/categories/{category_id}/activate — Activate (E2E)."""

    @pytest.mark.anyio
    async def test_activate_category_200(self, e2e_client):
        """Activate category returns 200 with is_active=True."""
        create_resp = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category To Activate", "slug": "e2e-category-to-activate"},
        )
        category_id = create_resp.json()["id"]

        # Deactivate first
        await e2e_client.post(
            f"/api/v1/categories/{category_id}/deactivate",
            json={"reason": "Testing activate"},
        )

        response = await e2e_client.post(
            f"/api/v1/categories/{category_id}/activate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


class TestCategoryDeactivateE2E:
    """POST /api/v1/categories/{category_id}/deactivate — Deactivate (E2E)."""

    @pytest.mark.anyio
    async def test_deactivate_category_200(self, e2e_client):
        """Deactivate category returns 200 with is_active=False."""
        create_resp = await e2e_client.post(
            "/api/v1/categories",
            json={"name": "E2E Category To Deactivate", "slug": "e2e-category-to-deactivate"},
        )
        category_id = create_resp.json()["id"]

        response = await e2e_client.post(
            f"/api/v1/categories/{category_id}/deactivate",
            json={"reason": "Testing deactivate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
