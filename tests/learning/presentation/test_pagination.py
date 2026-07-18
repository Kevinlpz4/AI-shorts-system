"""Tests for PaginatedResponse schema."""
from __future__ import annotations

from learning.presentation.schemas.responses import PaginatedResponse


class TestPagination:
    """PaginatedResponse test suite."""

    def test_paginated_response_schema(self):
        pr = PaginatedResponse(
            items=[1, 2, 3],
            total=10,
            page=1,
            page_size=3,
            has_next=True,
        )
        assert pr.total == 10
        assert pr.page == 1
        assert pr.page_size == 3
        assert pr.has_next is True

    def test_paginated_response_empty_items(self):
        pr = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            page_size=10,
            has_next=False,
        )
        assert pr.items == []
        assert pr.total == 0
        assert pr.has_next is False

    def test_paginated_response_serializable(self):
        pr = PaginatedResponse(
            items=["a", "b"],
            total=5,
            page=2,
            page_size=2,
            has_next=True,
        )
        d = pr.model_dump()
        assert isinstance(d, dict)
        assert d["items"] == ["a", "b"]
        assert d["total"] == 5
        assert d["page"] == 2
        assert d["has_next"] is True

    def test_paginated_response_last_page(self):
        pr = PaginatedResponse(
            items=[42],
            total=42,
            page=5,
            page_size=10,
            has_next=False,
        )
        assert pr.has_next is False
        assert len(pr.items) == 1

    def test_paginated_response_with_nested_dicts(self):
        pr = PaginatedResponse(
            items=[{"name": "test", "value": 42}],
            total=1,
            page=1,
            page_size=10,
            has_next=False,
        )
        assert pr.items[0]["name"] == "test"
        assert pr.items[0]["value"] == 42
