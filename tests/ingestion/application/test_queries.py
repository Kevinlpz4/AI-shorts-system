"""Tests for all Query dataclasses — 6 queries, 3 files."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ingestion.application.queries import (
    FindArticleQuery,
    FindFeedQuery,
    FindSourceQuery,
    ListActiveSourcesQuery,
    ListArticlesQuery,
    ListFeedsQuery,
)


class TestFindSourceQuery:
    """FindSourceQuery — Buscar fuente por ID."""

    def test_creates(self) -> None:
        q = FindSourceQuery(source_id="src-1")
        assert q.source_id == "src-1"


class TestListActiveSourcesQuery:
    """ListActiveSourcesQuery — Listar fuentes activas."""

    def test_creates_empty(self) -> None:
        q = ListActiveSourcesQuery()
        # No fields — verificar que existe y es frozen
        assert isinstance(q, ListActiveSourcesQuery)


class TestFindFeedQuery:
    """FindFeedQuery — Buscar feed por ID."""

    def test_creates(self) -> None:
        q = FindFeedQuery(feed_id="feed-1")
        assert q.feed_id == "feed-1"


class TestListFeedsQuery:
    """ListFeedsQuery — Listar feeds por fuente."""

    def test_creates_with_required_only(self) -> None:
        q = ListFeedsQuery(source_id="src-1")
        assert q.source_id == "src-1"
        assert q.page == 1
        assert q.size == 50

    def test_creates_with_pagination(self) -> None:
        q = ListFeedsQuery(source_id="src-1", page=2, size=10)
        assert q.page == 2
        assert q.size == 10


class TestFindArticleQuery:
    """FindArticleQuery — Buscar artículo por ID."""

    def test_creates(self) -> None:
        q = FindArticleQuery(article_id="art-1")
        assert q.article_id == "art-1"


class TestListArticlesQuery:
    """ListArticlesQuery — Listar artículos por feed."""

    def test_creates_with_required_only(self) -> None:
        q = ListArticlesQuery(feed_id="feed-1")
        assert q.feed_id == "feed-1"
        assert q.page == 1
        assert q.size == 50

    def test_creates_with_pagination(self) -> None:
        q = ListArticlesQuery(feed_id="feed-1", page=3, size=25)
        assert q.page == 3
        assert q.size == 25


class TestQueryImmutability:
    """All queries must be frozen dataclasses."""

    @pytest.mark.parametrize(
        "q_factory,field_name",
        [
            (lambda: FindSourceQuery(source_id="x"), "source_id"),
            (lambda: FindFeedQuery(feed_id="x"), "feed_id"),
            (lambda: ListFeedsQuery(source_id="x"), "source_id"),
            (lambda: FindArticleQuery(article_id="x"), "article_id"),
            (lambda: ListArticlesQuery(feed_id="x"), "feed_id"),
        ],
    )
    def test_all_queries_are_frozen(self, q_factory, field_name) -> None:
        q = q_factory()
        with pytest.raises(FrozenInstanceError):
            setattr(q, field_name, "mutated")

    def test_list_active_sources_is_frozen(self) -> None:
        """ListActiveSourcesQuery has no fields — verify frozen via hash behavior."""
        q = ListActiveSourcesQuery()
        # A frozen dataclass is also hashable if eq=True (default)
        assert hash(q) is not None
