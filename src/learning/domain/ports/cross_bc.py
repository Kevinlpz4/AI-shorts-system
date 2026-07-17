"""
Cross-BC Port Definitions for the Learning Bounded Context.

These are READ-ONLY Protocol ports that allow the Learning BC to
access data from other Bounded Contexts without coupling to their
internal models. All methods return plain data or Result types.

Future integration: Ingestion BC and Research BC implementations
will provide concrete adapters.
"""
from __future__ import annotations

from typing import Protocol

from foundation.result.result import Result


class IngestionReader(Protocol):
    """Read-only access to Ingestion BC data.

    Used by the Learning BC to extract features from articles
    and access source configuration without coupling to Ingestion internals.
    """

    def get_article_features(self, article_id: str) -> Result[dict]:
        """Get extracted features for an article.

        Args:
            article_id: String ID of the article.

        Returns:
            Ok(dict) with feature data if found.
            Error if article not found.
        """
        ...

    def get_source_config(self, source_name: str) -> Result[dict]:
        """Get configuration for a news source.

        Args:
            source_name: Name of the source.

        Returns:
            Ok(dict) with source config if found.
            Error if source not found.
        """
        ...


class ResearchReader(Protocol):
    """Read-only access to Research BC data.

    Used by the Learning BC to access topic scores and details
    without coupling to Research internals.
    """

    def get_topic_score(self, topic_id: str) -> Result[dict]:
        """Get the current score for a topic.

        Args:
            topic_id: String ID of the topic.

        Returns:
            Ok(dict) with score data if found.
            Error if topic not found.
        """
        ...

    def get_topic_details(self, topic_id: str) -> Result[dict]:
        """Get detailed information about a topic.

        Args:
            topic_id: String ID of the topic.

        Returns:
            Ok(dict) with topic details if found.
            Error if topic not found.
        """
        ...
