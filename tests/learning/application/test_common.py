"""Tests for Common types — QueryResult and PaginatedDTO (from common module)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from learning.application.common import PaginatedDTO, QueryResult


class TestQueryResult:
    """QueryResult[T] — resultado paginado de una consulta."""

    def test_creates_with_all_fields(self) -> None:
        result = QueryResult(
            data=["item1", "item2"],
            total=10,
            page=1,
            size=5,
        )
        assert result.data == ["item1", "item2"]
        assert result.total == 10
        assert result.page == 1
        assert result.size == 5

    def test_creates_with_defaults(self) -> None:
        result = QueryResult(data=[])
        assert result.data == []
        assert result.total is None
        assert result.page is None
        assert result.size is None

    def test_is_frozen(self) -> None:
        result = QueryResult(data=["x"])
        with pytest.raises(FrozenInstanceError):
            result.data = []  # type: ignore[misc]

    def test_equality(self) -> None:
        result1 = QueryResult(data=["a"], total=1, page=1, size=10)
        result2 = QueryResult(data=["a"], total=1, page=1, size=10)
        assert result1 == result2

    def test_empty_data(self) -> None:
        result = QueryResult(data=[], total=0)
        assert len(result.data) == 0
        assert result.total == 0


class TestCommonPaginatedDTO:
    """PaginatedDTO[T] from common module — with calculated pages property."""

    def test_creates(self) -> None:
        page = PaginatedDTO(
            data=["item1", "item2"],
            total=10,
            page=1,
            size=5,
        )
        assert page.data == ["item1", "item2"]
        assert page.total == 10
        assert page.page == 1
        assert page.size == 5

    def test_pages_calculation_zero_items(self) -> None:
        page = PaginatedDTO(data=[], total=0, page=1, size=50)
        assert page.pages == 0

    def test_pages_calculation_exact_division(self) -> None:
        """100 items / 50 per page = 2 pages (exact)."""
        page = PaginatedDTO(data=[], total=100, page=1, size=50)
        assert page.pages == 2

    def test_pages_calculation_with_remainder(self) -> None:
        """42 items / 50 per page = 1 page (remainder rounds up)."""
        page = PaginatedDTO(data=[], total=42, page=1, size=50)
        assert page.pages == 1

    def test_pages_calculation_many_items(self) -> None:
        """150 items / 50 per page = 3 pages (exact)."""
        page = PaginatedDTO(data=[], total=150, page=1, size=50)
        assert page.pages == 3

    def test_pages_calculation_odd_remainder(self) -> None:
        """51 items / 50 per page = 2 pages (1 remainder)."""
        page = PaginatedDTO(data=[], total=51, page=1, size=50)
        assert page.pages == 2

    def test_pages_calculation_one_item(self) -> None:
        """1 item / 50 per page = 1 page."""
        page = PaginatedDTO(data=[], total=1, page=1, size=50)
        assert page.pages == 1

    def test_pages_calculation_single_page_size(self) -> None:
        """5 items / 5 per page = 1 page."""
        page = PaginatedDTO(data=[], total=5, page=1, size=5)
        assert page.pages == 1

    def test_is_frozen(self) -> None:
        page = PaginatedDTO(data=[], total=0, page=1, size=50)
        with pytest.raises(FrozenInstanceError):
            page.total = 10  # type: ignore[misc]

    def test_equality(self) -> None:
        page1 = PaginatedDTO(data=["a"], total=1, page=1, size=10)
        page2 = PaginatedDTO(data=["a"], total=1, page=1, size=10)
        assert page1 == page2

    def test_data_is_list(self) -> None:
        """Common PaginatedDTO uses list, not tuple."""
        page = PaginatedDTO(data=["a", "b"], total=2, page=1, size=10)
        assert isinstance(page.data, list)
