"""Tests for QueryResult[T] generic."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ingestion.application.common import QueryResult


class TestQueryResult:
    """Verifies QueryResult construction and usage."""

    def test_construction_with_all_fields(self) -> None:
        result = QueryResult(
            data=[1, 2, 3],
            total=100,
            page=1,
            size=50,
        )
        assert result.data == [1, 2, 3]
        assert result.total == 100
        assert result.page == 1
        assert result.size == 50

    def test_construction_with_defaults(self) -> None:
        """total, page, size should default to None."""
        result = QueryResult(data=["a", "b"])
        assert result.data == ["a", "b"]
        assert result.total is None
        assert result.page is None
        assert result.size is None

    def test_construction_with_partial_defaults(self) -> None:
        result = QueryResult(data=[], total=0)
        assert result.data == []
        assert result.total == 0
        assert result.page is None
        assert result.size is None

    def test_empty_data(self) -> None:
        result = QueryResult(data=[])
        assert result.data == []

    def test_generic_with_integers(self) -> None:
        result: QueryResult[int] = QueryResult(data=[1, 2, 3])
        assert sum(result.data) == 6

    def test_generic_with_strings(self) -> None:
        result: QueryResult[str] = QueryResult(data=["a", "b"])
        assert "".join(result.data) == "ab"

    def test_generic_with_dicts(self) -> None:
        result: QueryResult[dict] = QueryResult(data=[{"id": 1}, {"id": 2}])
        assert len(result.data) == 2

    def test_immutable(self) -> None:
        """QueryResult must be frozen (immutable)."""
        result = QueryResult(data=[1])
        with pytest.raises(FrozenInstanceError):
            result.data = [2]  # type: ignore[misc]

    def test_immutable_nested(self) -> None:
        result = QueryResult(data=[1])
        with pytest.raises(FrozenInstanceError):
            result.total = 999  # type: ignore[misc]

    def test_iterate_data(self) -> None:
        result = QueryResult(data=[10, 20, 30])
        assert list(result.data) == [10, 20, 30]

    def test_length_of_data(self) -> None:
        result = QueryResult(data=[1, 2, 3, 4, 5])
        assert len(result.data) == 5

    def test_equality(self) -> None:
        """Two QueryResults with same values must be equal."""
        r1 = QueryResult(data=[1], total=10, page=1, size=5)
        r2 = QueryResult(data=[1], total=10, page=1, size=5)
        assert r1 == r2

    def test_inequality(self) -> None:
        r1 = QueryResult(data=[1], total=10, page=1, size=5)
        r2 = QueryResult(data=[2], total=10, page=1, size=5)
        assert r1 != r2
