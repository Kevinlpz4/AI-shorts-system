"""Tests for IngestionErrorCode enum."""

from __future__ import annotations

from ingestion.domain.exceptions.errors import IngestionErrorCode


class TestIngestionErrorCode:
    def test_all_codes_defined(self) -> None:
        expected_codes = {
            "NEWS_SOURCE_NOT_FOUND",
            "FEED_NOT_FOUND",
            "RAW_ARTICLE_NOT_FOUND",
            "CATEGORY_NOT_FOUND",
            "TOPIC_NOT_FOUND",
            "DUPLICATE_NEWS_SOURCE",
            "DUPLICATE_FEED_URL",
            "DUPLICATE_ARTICLE",
            "INVALID_SOURCE_URL",
            "INVALID_ARTICLE_URL",
            "INVALID_LANGUAGE",
            "NEWS_SOURCE_INACTIVE",
            "FEED_INACTIVE",
            "HAS_ACTIVE_FEEDS",
            "CYCLE_DETECTED",
            "FEED_MAX_RETRIES_EXCEEDED",
            "FEED_ALREADY_PAUSED",
        }
        actual_codes = {code.value for code in IngestionErrorCode}
        assert actual_codes == expected_codes

    def test_str_enum_values(self) -> None:
        assert IngestionErrorCode.NEWS_SOURCE_NOT_FOUND == "NEWS_SOURCE_NOT_FOUND"
        assert IngestionErrorCode.FEED_NOT_FOUND == "FEED_NOT_FOUND"
        assert IngestionErrorCode.DUPLICATE_ARTICLE == "DUPLICATE_ARTICLE"
        assert IngestionErrorCode.CYCLE_DETECTED == "CYCLE_DETECTED"

    def test_members_count(self) -> None:
        assert len(IngestionErrorCode) == 17
