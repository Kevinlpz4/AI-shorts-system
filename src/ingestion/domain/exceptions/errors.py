"""
Ingestion Error Codes — ADR-022 compliant.

Each Bounded Context defines its own ``str, Enum`` independent of Foundation's
``ErrorCode``. This follows ADR-022 which specifies that ErrorCodes are NOT
extensible by inheritance (Python 3.11+ forbids subclassing Enums with members).

Usage::

    from ingestion.domain.exceptions.errors import IngestionErrorCode

    error = Error(code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND, message="...")
"""

from __future__ import annotations

from enum import Enum


class IngestionErrorCode(str, Enum):
    """Error codes for the Ingestion Bounded Context.

    Each code represents a well-known failure scenario in the domain.
    Used with ``Result.failure(Error(code=..., message=...))`` in repository
    ports and application services.
    """

    NEWS_SOURCE_NOT_FOUND = "NEWS_SOURCE_NOT_FOUND"
    FEED_NOT_FOUND = "FEED_NOT_FOUND"
    RAW_ARTICLE_NOT_FOUND = "RAW_ARTICLE_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    TOPIC_NOT_FOUND = "TOPIC_NOT_FOUND"
    DUPLICATE_NEWS_SOURCE = "DUPLICATE_NEWS_SOURCE"
    DUPLICATE_FEED_URL = "DUPLICATE_FEED_URL"
    DUPLICATE_ARTICLE = "DUPLICATE_ARTICLE"
    INVALID_SOURCE_URL = "INVALID_SOURCE_URL"
    INVALID_ARTICLE_URL = "INVALID_ARTICLE_URL"
    INVALID_LANGUAGE = "INVALID_LANGUAGE"
    NEWS_SOURCE_INACTIVE = "NEWS_SOURCE_INACTIVE"
    FEED_INACTIVE = "FEED_INACTIVE"
    HAS_ACTIVE_FEEDS = "HAS_ACTIVE_FEEDS"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    FEED_MAX_RETRIES_EXCEEDED = "FEED_MAX_RETRIES_EXCEEDED"
    FEED_ALREADY_PAUSED = "FEED_ALREADY_PAUSED"
