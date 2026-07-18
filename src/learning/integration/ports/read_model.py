"""
Read Model Ports — Protocol-based ports for cross-BC data access.

These ports define read-only access to data owned by other BCs.
Learning uses these to query articles, sources, and topics
without creating dependencies on other BCs' internal models.
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result


class ArticleReadModel(Protocol):
    """Read-only access to article data from Ingestion BC.

    Provides query methods for article data. All methods return
    Result types — never raise exceptions for "not found" cases.
    """

    def get_article(self, article_id: str) -> Result[dict]:
        """Get a single article by ID."""
        ...

    def get_articles_by_source(self, source_name: str, limit: int = 50) -> Result[list[dict]]:
        """Get articles filtered by source name."""
        ...


class SourceReadModel(Protocol):
    """Read-only access to source data from Ingestion BC.

    Provides query methods for source configuration and metadata.
    """

    def get_source(self, source_name: str) -> Result[dict]:
        """Get a single source by name."""
        ...

    def get_all_sources(self) -> Result[list[dict]]:
        """Get all registered sources."""
        ...


class TopicReadModel(Protocol):
    """Read-only access to topic data from Research BC.

    Provides query methods for topic information and scores.
    """

    def get_topic(self, topic_id: str) -> Result[dict]:
        """Get a single topic by ID."""
        ...

    def get_topic_score(self, topic_id: str) -> Result[float]:
        """Get the current score for a topic."""
        ...
