"""
InMemory Cross-BC Adapters for the Learning Bounded Context.

Provides InMemory implementations of the cross-BC reader ports:
    - InMemoryIngestionReader: read-only access to Ingestion BC data
    - InMemoryResearchReader: read-only access to Research BC data

These adapters use plain dicts for storage and are intended for
testing only. They implement the Protocol ports defined in
``learning.domain.ports.cross_bc``.
"""
from __future__ import annotations

from foundation.result.result import Error, ErrorCode, Result


class InMemoryIngestionReader:
    """InMemory implementation of IngestionReader port.

    Provides read-only access to article features and source
    configuration from the Ingestion BC during testing.

    Data is injected at construction time — no external dependencies.

    Usage::

        articles = {"a1": {"title": "...", "keywords": ["ai", "llm"]}}
        sources = {"reuters": {"name": "reuters", "quality": 0.9}}
        reader = InMemoryIngestionReader(articles=articles, sources=sources)
        result = reader.get_article_features("a1")
        assert result.is_success
    """

    def __init__(
        self,
        articles: dict[str, dict] | None = None,
        sources: dict[str, dict] | None = None,
    ) -> None:
        self._articles = articles or {}
        self._sources = sources or {}

    def get_article_features(self, article_id: str) -> Result[dict]:
        """Get extracted features for an article."""
        if article_id not in self._articles:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Article '{article_id}' not found",
                )
            )
        return Result.success(self._articles[article_id])

    def get_source_config(self, source_name: str) -> Result[dict]:
        """Get configuration for a news source."""
        if source_name not in self._sources:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Source '{source_name}' not found",
                )
            )
        return Result.success(self._sources[source_name])


class InMemoryResearchReader:
    """InMemory implementation of ResearchReader port.

    Provides read-only access to topic scores and details
    from the Research BC during testing.

    Data is injected at construction time — no external dependencies.

    Usage::

        topics = {"t1": {"title": "AI News", "score": 0.85, "keywords": [...]}}
        reader = InMemoryResearchReader(topics=topics)
        result = reader.get_topic_score("t1")
        assert result.is_success
    """

    def __init__(self, topics: dict[str, dict] | None = None) -> None:
        self._topics = topics or {}

    def get_topic_score(self, topic_id: str) -> Result[dict]:
        """Get the current score for a topic."""
        if topic_id not in self._topics:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Topic '{topic_id}' not found",
                )
            )
        return Result.success({"score": self._topics[topic_id].get("score", 0.0)})

    def get_topic_details(self, topic_id: str) -> Result[dict]:
        """Get detailed information about a topic."""
        if topic_id not in self._topics:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Topic '{topic_id}' not found",
                )
            )
        return Result.success(self._topics[topic_id])
