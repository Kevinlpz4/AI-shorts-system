"""Tests for PaginatedDTO[T] generic."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ingestion.application.common import PaginatedDTO


class TestPaginatedDTO:
    """Verifies PaginatedDTO construction, pages calculation, and immutability."""

    # ── Construction ──

    def test_construction(self) -> None:
        page = PaginatedDTO(data=[1, 2, 3], total=100, page=1, size=50)
        assert page.data == [1, 2, 3]
        assert page.total == 100
        assert page.page == 1
        assert page.size == 50

    def test_empty_data(self) -> None:
        page = PaginatedDTO(data=[], total=0, page=1, size=50)
        assert page.data == []

    def test_generic_with_strings(self) -> None:
        page: PaginatedDTO[str] = PaginatedDTO(
            data=["a", "b"],
            total=2,
            page=1,
            size=10,
        )
        assert len(page.data) == 2

    # ── Pages calculation ──

    def test_pages_exact_division(self) -> None:
        """50 items, 10 per page → exactly 5 pages."""
        page = PaginatedDTO(data=list(range(10)), total=50, page=1, size=10)
        assert page.pages == 5

    def test_pages_round_up(self) -> None:
        """51 items, 10 per page → 6 pages (5 full + 1 partial)."""
        page = PaginatedDTO(data=list(range(10)), total=51, page=1, size=10)
        assert page.pages == 6

    def test_pages_single_item(self) -> None:
        """1 item, 10 per page → 1 page."""
        page = PaginatedDTO(data=[1], total=1, page=1, size=10)
        assert page.pages == 1

    def test_pages_exactly_one_page(self) -> None:
        """10 items, 10 per page → 1 page."""
        page = PaginatedDTO(data=list(range(10)), total=10, page=1, size=10)
        assert page.pages == 1

    def test_pages_zero_total(self) -> None:
        """0 items → 0 pages."""
        page = PaginatedDTO(data=[], total=0, page=1, size=10)
        assert page.pages == 0

    def test_pages_large_numbers(self) -> None:
        """1000 items, 50 per page → 20 pages."""
        page = PaginatedDTO(data=list(range(50)), total=1000, page=1, size=50)
        assert page.pages == 20

    def test_pages_less_than_page_size(self) -> None:
        """3 items, 10 per page → 1 page."""
        page = PaginatedDTO(data=[1, 2, 3], total=3, page=1, size=10)
        assert page.pages == 1

    # ── Immutability ──

    def test_immutable_data(self) -> None:
        page = PaginatedDTO(data=[1], total=1, page=1, size=10)
        with pytest.raises(FrozenInstanceError):
            page.data = [2]  # type: ignore[misc]

    def test_immutable_total(self) -> None:
        page = PaginatedDTO(data=[1], total=1, page=1, size=10)
        with pytest.raises(FrozenInstanceError):
            page.total = 999  # type: ignore[misc]

    def test_immutable_page(self) -> None:
        page = PaginatedDTO(data=[1], total=1, page=1, size=10)
        with pytest.raises(FrozenInstanceError):
            page.page = 2  # type: ignore[misc]

    # ── Equality ──

    def test_equality(self) -> None:
        p1 = PaginatedDTO(data=[1], total=10, page=1, size=5)
        p2 = PaginatedDTO(data=[1], total=10, page=1, size=5)
        assert p1 == p2

    def test_inequality(self) -> None:
        p1 = PaginatedDTO(data=[1], total=10, page=1, size=5)
        p2 = PaginatedDTO(data=[2], total=10, page=1, size=5)
        assert p1 != p2

    # ── Edge cases ──

    def test_size_of_one(self) -> None:
        """Edge case: size=1 means each page has exactly 1 item."""
        page = PaginatedDTO(data=[1], total=5, page=1, size=1)
        assert page.pages == 5

    def test_page_property(self) -> None:
        """page must preserve its value from construction."""
        page = PaginatedDTO(data=[1], total=10, page=3, size=5)
        assert page.page == 3

    def test_size_property(self) -> None:
        page = PaginatedDTO(data=[1], total=10, page=1, size=25)
        assert page.size == 25
