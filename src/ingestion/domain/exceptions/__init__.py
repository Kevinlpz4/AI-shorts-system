"""
Ingestion Domain Exception Hierarchy — ADR-022 compliant.

Each error inherits from ``IngestionError → DomainError → FoundationError``
for full hierarchy compatibility AND from ``ValueError`` for backward
compatibility with existing domain code that catches ``ValueError`` directly.

Usage::

    from ingestion.domain.exceptions import InvalidSourceUrlError

    raise InvalidSourceUrlError("Source URL must not be empty")
"""

from __future__ import annotations

from foundation import DomainError


class IngestionError(DomainError, ValueError):
    """Base error for all Ingestion BC domain exceptions.

    Inherits from both ``DomainError`` (for domain hierarchy) and
    ``ValueError`` (for backward compatibility with existing code that
    catches ``ValueError`` directly).
    """

    code = "INGESTION_ERROR"

    def __str__(self) -> str:
        """Return the message (not detail) for backward-compatible str().

        FoundationError stores the message separately and passes detail
        to parent Exception. Override so that ``str(error)`` returns
        the human-readable message, matching the behavior of ``ValueError``.
        """
        return self.message or self.detail


# ── General Purpose Errors ──


class InvalidStateError(IngestionError):
    """Raised when an Entity or Aggregate is in an invalid state.

    Use this for general invariant violations that don't have a
    more specific error class.
    """

    code = "INVALID_STATE"


# ── Source Errors ──


class SourceError(IngestionError):
    """Base for NewsSource-related errors."""

    code = "SOURCE_ERROR"


class InvalidSourceUrlError(SourceError):
    """Raised when a NewsSource URL is invalid."""

    code = "INVALID_SOURCE_URL"


class SourceAlreadyEnabledError(SourceError):
    """Raised when trying to enable an already-enabled NewsSource."""

    code = "SOURCE_ALREADY_ENABLED"


class SourceAlreadyDisabledError(SourceError):
    """Raised when trying to disable an already-disabled NewsSource."""

    code = "SOURCE_ALREADY_DISABLED"


# ── Feed Errors ──


class FeedError(IngestionError):
    """Base for Feed-related errors."""

    code = "FEED_ERROR"


class FeedAlreadyEnabledError(FeedError):
    """Raised when trying to enable an already-enabled Feed."""

    code = "FEED_ALREADY_ENABLED"


class FeedAlreadyDisabledError(FeedError):
    """Raised when trying to disable an already-disabled Feed."""

    code = "FEED_ALREADY_DISABLED"


class FeedAlreadyPausedError(FeedError):
    """Raised when trying to pause an already-paused Feed."""

    code = "FEED_ALREADY_PAUSED"


class FeedMaxRetriesExceededError(FeedError):
    """Raised when a Feed has exceeded its maximum retry count."""

    code = "FEED_MAX_RETRIES_EXCEEDED"


# ── RawArticle Errors ──


class RawArticleError(IngestionError):
    """Base for RawArticle-related errors."""

    code = "RAW_ARTICLE_ERROR"


class InvalidArticleUrlError(RawArticleError):
    """Raised when an Article URL is invalid."""

    code = "INVALID_ARTICLE_URL"


class InvalidArticleTitleError(RawArticleError):
    """Raised when an Article title is invalid."""

    code = "INVALID_ARTICLE_TITLE"


# ── Category Errors ──


class CategoryError(IngestionError):
    """Base for Category-related errors."""

    code = "CATEGORY_ERROR"


class InvalidCategoryError(CategoryError):
    """Raised when a Category name or reference is invalid."""

    code = "INVALID_CATEGORY"


class DuplicateCategoryNameError(CategoryError):
    """Raised when a duplicate category name is detected."""

    code = "DUPLICATE_CATEGORY_NAME"


class CycleDetectedError(CategoryError):
    """Raised when a circular hierarchy is detected in categories."""

    code = "CYCLE_DETECTED"


# ── Topic Errors ──


class TopicError(IngestionError):
    """Base for Topic-related errors."""

    code = "TOPIC_ERROR"


class InvalidTopicError(TopicError):
    """Raised when a Topic name or reference is invalid."""

    code = "INVALID_TOPIC"


# ── Validation Errors ──


class ValidationError(IngestionError):
    """Base for general validation errors.

    Includes sync policy and language validation.
    """

    code = "VALIDATION_ERROR"


class InvalidSyncPolicyError(ValidationError):
    """Raised when SyncPolicy configuration is invalid."""

    code = "INVALID_SYNC_POLICY"


class InvalidLanguageError(ValidationError):
    """Raised when a Language code is invalid."""

    code = "INVALID_LANGUAGE"


__all__ = [
    "IngestionError",
    "InvalidStateError",
    "SourceError",
    "InvalidSourceUrlError",
    "SourceAlreadyEnabledError",
    "SourceAlreadyDisabledError",
    "FeedError",
    "FeedAlreadyEnabledError",
    "FeedAlreadyDisabledError",
    "FeedAlreadyPausedError",
    "FeedMaxRetriesExceededError",
    "RawArticleError",
    "InvalidArticleUrlError",
    "InvalidArticleTitleError",
    "CategoryError",
    "InvalidCategoryError",
    "DuplicateCategoryNameError",
    "CycleDetectedError",
    "TopicError",
    "InvalidTopicError",
    "ValidationError",
    "InvalidSyncPolicyError",
    "InvalidLanguageError",
]
