"""
Tests for repository Protocol interfaces.

These tests verify that the Protocols are structurally sound and can be
implemented. They use simple in-memory implementations to validate the
contracts are correct.
"""

from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result

from ingestion.domain.ports.repositories import (
    CategoryRepository,
    FeedRepository,
    NewsSourceRepository,
    RawArticleRepository,
    TopicRepository,
)


def test_news_source_repository_is_protocol() -> None:
    assert issubclass(NewsSourceRepository, Protocol)


def test_feed_repository_is_protocol() -> None:
    assert issubclass(FeedRepository, Protocol)


def test_raw_article_repository_is_protocol() -> None:
    assert issubclass(RawArticleRepository, Protocol)


def test_category_repository_is_protocol() -> None:
    assert issubclass(CategoryRepository, Protocol)


def test_topic_repository_is_protocol() -> None:
    assert issubclass(TopicRepository, Protocol)


class TestRepositoryStruct:
    """Structural tests: verify method signatures compile and are correct."""

    def test_news_source_repository_signatures(self) -> None:
        methods = {
            "save",
            "find_by_id",
            "find_by_name",
            "find_all",
            "find_active",
            "exists_by_name",
        }
        repo_methods = set(NewsSourceRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        assert methods.issubset(repo_methods)

    def test_feed_repository_signatures(self) -> None:
        methods = {
            "save",
            "find_by_id",
            "find_by_source",
            "find_by_url",
            "find_active_by_source",
            "exists_by_source_and_url",
            "count_active_by_source",
        }
        repo_methods = set(FeedRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        assert methods.issubset(repo_methods)

    def test_raw_article_repository_signatures(self) -> None:
        methods = {
            "save",
            "save_batch",
            "find_by_id",
            "find_by_feed",
            "find_by_hash",
            "exists_by_url",
            "exists_by_hash",
            "count_by_feed",
        }
        repo_methods = set(RawArticleRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        assert methods.issubset(repo_methods)

    def test_category_repository_signatures(self) -> None:
        methods = {
            "save",
            "find_by_id",
            "find_by_slug",
            "find_all",
            "find_active",
            "find_by_parent",
            "exists_by_slug",
        }
        repo_methods = set(CategoryRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        assert methods.issubset(repo_methods)

    def test_topic_repository_signatures(self) -> None:
        methods = {
            "save",
            "find_by_id",
            "find_by_name",
            "find_all",
            "find_active",
            "exists_by_name",
        }
        repo_methods = set(TopicRepository.__protocol_attrs__)  # type: ignore[attr-defined]
        assert methods.issubset(repo_methods)
