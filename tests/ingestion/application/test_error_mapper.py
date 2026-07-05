"""Tests for ErrorMapper — domain → application error conversion."""

from __future__ import annotations

from enum import Enum

from foundation.errors.base import DomainError
from foundation.result.result import Error, ErrorCode

from ingestion.application.errors import ErrorMapper
from ingestion.application.exceptions import ApplicationErrorCode
from ingestion.domain.exceptions import (
    CycleDetectedError,
    DuplicateCategoryNameError,
    FeedAlreadyPausedError,
    FeedMaxRetriesExceededError,
    InvalidArticleUrlError,
    InvalidCategoryError,
    InvalidLanguageError,
    InvalidSourceUrlError,
    InvalidStateError,
    InvalidSyncPolicyError,
    InvalidTopicError,
    SourceAlreadyDisabledError,
    SourceAlreadyEnabledError,
)


class TestErrorMapperMapDomainError:
    """Tests for ErrorMapper.map_domain_error() with actual domain exceptions."""

    def test_maps_invalid_source_url(self) -> None:
        error = InvalidSourceUrlError("Bad source URL")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID
        assert "Bad source URL" in result.message

    def test_maps_source_already_enabled(self) -> None:
        error = SourceAlreadyEnabledError("Already enabled")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_source_already_disabled(self) -> None:
        error = SourceAlreadyDisabledError("Already disabled")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_feed_already_paused(self) -> None:
        error = FeedAlreadyPausedError("Already paused")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_max_retries_exceeded(self) -> None:
        error = FeedMaxRetriesExceededError("Max retries exceeded")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_invalid_article_url(self) -> None:
        error = InvalidArticleUrlError("Bad article URL")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_language(self) -> None:
        error = InvalidLanguageError("Bad language code")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_category(self) -> None:
        error = InvalidCategoryError("Bad category")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_duplicate_category_name(self) -> None:
        error = DuplicateCategoryNameError("Duplicate category")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_cycle_detected(self) -> None:
        error = CycleDetectedError("Cycle detected in hierarchy")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_topic(self) -> None:
        error = InvalidTopicError("Bad topic")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_state(self) -> None:
        error = InvalidStateError("Invalid state")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_invalid_sync_policy(self) -> None:
        error = InvalidSyncPolicyError("Bad sync policy")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_preserves_message_and_detail(self) -> None:
        error = InvalidCategoryError("Bad category", detail="Additional info")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID
        assert result.message == "Bad category"
        assert result.detail == "Additional info"

    def test_maps_unknown_code_to_operation_failed(self) -> None:
        """Unknown error codes fall back to OPERATION_FAILED."""
        error = _UnknownDomainError("Something unexpected")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED
        assert result.message == "Something unexpected"


class TestErrorMapperMapResultError:
    """Tests for ErrorMapper.map_result_error() mapping Result errors."""

    def test_preserves_already_mapped_code(self) -> None:
        """If the Error already has an ApplicationErrorCode, return as-is."""
        error = Error(code=ApplicationErrorCode.COMMAND_INVALID, message="test")
        result = ErrorMapper.map_result_error(error)
        assert result is error  # same object identity

    def test_maps_foundation_unknown_to_operation_failed(self) -> None:
        """Foundation ErrorCode.UNKNOWN maps to OPERATION_FAILED."""
        error = Error(code=ErrorCode.UNKNOWN, message="Unknown error")
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_domain_news_source_not_found(self) -> None:
        """Error with IngestionErrorCode NEWS_SOURCE_NOT_FOUND → RESOURCE_NOT_FOUND."""
        error = Error(
            code=_IngestionErrorCodeStub.NEWS_SOURCE_NOT_FOUND,
            message="Source not found",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert result.message == "Source not found"

    def test_maps_domain_feed_not_found(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.FEED_NOT_FOUND,
            message="Feed missing",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_domain_duplicate_source(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.DUPLICATE_NEWS_SOURCE,
            message="Duplicate",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_domain_category_not_found(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.CATEGORY_NOT_FOUND,
            message="Category not found",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_domain_topic_not_found(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.TOPIC_NOT_FOUND,
            message="Topic not found",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_domain_article_not_found(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.RAW_ARTICLE_NOT_FOUND,
            message="Article not found",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_preserves_message_and_detail(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.FEED_NOT_FOUND,
            message="Feed missing",
            detail="No feed with id=123",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert result.message == "Feed missing"
        assert result.detail == "No feed with id=123"

    def test_maps_inactive_code(self) -> None:
        error = Error(
            code=_IngestionErrorCodeStub.NEWS_SOURCE_INACTIVE,
            message="Source is inactive",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID


# ── Helpers ──


class _IngestionErrorCodeStub(str, Enum):
    """Stub for domain IngestionErrorCode to test Result error mapping
    without coupling to the actual domain enum."""

    NEWS_SOURCE_NOT_FOUND = "NEWS_SOURCE_NOT_FOUND"
    FEED_NOT_FOUND = "FEED_NOT_FOUND"
    RAW_ARTICLE_NOT_FOUND = "RAW_ARTICLE_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    TOPIC_NOT_FOUND = "TOPIC_NOT_FOUND"
    DUPLICATE_NEWS_SOURCE = "DUPLICATE_NEWS_SOURCE"
    NEWS_SOURCE_INACTIVE = "NEWS_SOURCE_INACTIVE"


class _UnknownDomainError(DomainError):
    """Domain error with code not in the mapping dict."""

    code = "UNKNOWN_CODE_THAT_DOES_NOT_EXIST"
