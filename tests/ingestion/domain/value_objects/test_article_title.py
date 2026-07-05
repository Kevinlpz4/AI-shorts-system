"""Tests for ArticleTitle value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.article_title import MAX_TITLE_LENGTH, ArticleTitle


class TestArticleTitleValidation:
    def test_valid_title(self) -> None:
        title = ArticleTitle("Test Article")
        assert title.value == "Test Article"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArticleTitle("")

    def test_whitespace_only_trimmed_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArticleTitle("   ")

    def test_exceeds_max_length_raises(self) -> None:
        long_title = "x" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(ValueError, match="must not exceed"):
            ArticleTitle(long_title)

    def test_control_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="control characters"):
            ArticleTitle("Test\x00Article")

    def test_newline_within_title_raises(self) -> None:
        with pytest.raises(ValueError, match="control characters"):
            ArticleTitle("Test\nArticle")

    def test_tab_within_title_raises(self) -> None:
        with pytest.raises(ValueError, match="control characters"):
            ArticleTitle("Test\tArticle")

    def test_auto_trims_leading_spaces(self) -> None:
        title = ArticleTitle("  Hello World")
        assert title.value == "Hello World"

    def test_auto_trims_trailing_spaces(self) -> None:
        title = ArticleTitle("Hello World  ")
        assert title.value == "Hello World"

    def test_max_length_boundary(self) -> None:
        title = ArticleTitle("x" * MAX_TITLE_LENGTH)
        assert len(title.value) == MAX_TITLE_LENGTH

    def test_frozen_immutable(self) -> None:
        title = ArticleTitle("Test")
        with pytest.raises(Exception):
            title.value = "Changed"

    def test_equality_by_value(self) -> None:
        t1 = ArticleTitle("Test")
        t2 = ArticleTitle("Test")
        assert t1 == t2
