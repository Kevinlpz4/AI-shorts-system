"""Tests for ArticleUrl value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.article_url import ArticleUrl


class TestArticleUrlValidation:
    def test_valid_url(self) -> None:
        url = ArticleUrl("https://example.com/article/123")
        assert url.value == "https://example.com/article/123"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArticleUrl("")

    def test_ftp_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme must be http or https"):
            ArticleUrl("ftp://example.com")

    def test_no_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme must be http or https"):
            ArticleUrl("example.com")

    def test_no_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="must have a valid domain"):
            ArticleUrl("https://")

    def test_control_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="control characters"):
            ArticleUrl("https://example.com\npath")

    def test_frozen_immutable(self) -> None:
        url = ArticleUrl("https://example.com")
        with pytest.raises(Exception):
            url.value = "https://changed.com"

    def test_equality_by_value(self) -> None:
        url1 = ArticleUrl("https://example.com/a")
        url2 = ArticleUrl("https://example.com/a")
        assert url1 == url2


class TestArticleUrlMethods:
    def test_normalized_lowercases(self) -> None:
        url = ArticleUrl("HTTPS://EXAMPLE.COM/A")
        assert url.normalized() == "https://example.com/A"

    def test_normalized_strips_trailing_slash(self) -> None:
        url = ArticleUrl("https://example.com/a/")
        assert url.normalized() == "https://example.com/a"

    def test_domain_simple(self) -> None:
        url = ArticleUrl("https://reddit.com/r/programming")
        assert url.domain() == "reddit.com"

    def test_domain_subdomain(self) -> None:
        url = ArticleUrl("https://news.ycombinator.com/item?id=123")
        assert url.domain() == "news.ycombinator.com"

    def test_domain_with_www(self) -> None:
        url = ArticleUrl("https://www.example.com/page")
        assert url.domain() == "www.example.com"
