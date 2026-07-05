"""Tests for SourceUrl value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.source_url import SourceUrl


class TestSourceUrlValidation:
    def test_valid_http_url(self) -> None:
        url = SourceUrl("http://example.com")
        assert url.value == "http://example.com"

    def test_valid_https_url(self) -> None:
        url = SourceUrl("https://www.reddit.com")
        assert url.value == "https://www.reddit.com"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            SourceUrl("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            SourceUrl("   ")

    def test_ftp_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme must be http or https"):
            SourceUrl("ftp://example.com")

    def test_file_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme must be http or https"):
            SourceUrl("file:///tmp/test")

    def test_fragment_raises(self) -> None:
        with pytest.raises(ValueError, match="must not contain fragments"):
            SourceUrl("https://example.com#section")

    def test_no_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="scheme must be http or https"):
            SourceUrl("example.com")

    def test_no_domain_raises(self) -> None:
        with pytest.raises(ValueError, match="must have a valid domain"):
            SourceUrl("https://")

    def test_control_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="control characters"):
            SourceUrl("https://example.com\npath")

    def test_frozen_immutable(self) -> None:
        url = SourceUrl("https://example.com")
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            url.value = "https://changed.com"

    def test_equality_by_value(self) -> None:
        url1 = SourceUrl("https://example.com")
        url2 = SourceUrl("https://example.com")
        assert url1 == url2

    def test_inequality(self) -> None:
        url1 = SourceUrl("https://example.com")
        url2 = SourceUrl("https://other.com")
        assert url1 != url2


class TestSourceUrlNormalization:
    def test_normalized_lowercases_scheme(self) -> None:
        url = SourceUrl("HTTPS://EXAMPLE.COM")
        assert url.normalized() == "https://example.com"

    def test_normalized_lowercases_host(self) -> None:
        url = SourceUrl("https://EXAMPLE.COM")
        assert url.normalized() == "https://example.com"

    def test_normalized_strips_trailing_slash(self) -> None:
        url = SourceUrl("https://example.com/")
        assert url.normalized() == "https://example.com"

    def test_normalized_preserves_path(self) -> None:
        url = SourceUrl("https://example.com/path/to/page")
        assert url.normalized() == "https://example.com/path/to/page"

    def test_normalized_preserves_query(self) -> None:
        url = SourceUrl("https://example.com/page?q=test")
        assert url.normalized() == "https://example.com/page?q=test"

    def test_normalized_handles_mixed_case(self) -> None:
        url = SourceUrl("https://MyHost.COM/Path/")
        assert url.normalized() == "https://myhost.com/Path"
