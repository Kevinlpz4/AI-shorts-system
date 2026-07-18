"""
InMemory Read Model implementations for Learning BC integration.

Provides InMemory adapters for read model ports used in cross-BC
data access during testing. All methods return Result types —
never raise exceptions for "not found" cases.

Read models implement:
    - InMemoryArticleReadModel: read-only access to article data
    - InMemorySourceReadModel: read-only access to source data
    - InMemoryTopicReadModel: read-only access to topic data
"""
from __future__ import annotations

from foundation.result.result import Error, ErrorCode, Result


class InMemoryArticleReadModel:
    """InMemory implementation of ArticleReadModel port.

    Stores articles in a ``dict[str, dict]`` keyed by article_id.
    Data can be injected at construction time for test setup.

    Usage::

        articles = {"a1": {"id": "a1", "source_name": "reuters", "title": "..."}}
        model = InMemoryArticleReadModel(articles=articles)
        result = model.get_article("a1")
        assert result.is_success
    """

    def __init__(self, articles: dict[str, dict] | None = None) -> None:
        self._store = articles or {}

    def get_article(self, article_id: str) -> Result[dict]:
        """Get a single article by ID."""
        if article_id not in self._store:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Article '{article_id}' not found",
                )
            )
        return Result.success(self._store[article_id])

    def get_articles_by_source(self, source_name: str, limit: int = 50) -> Result[list[dict]]:
        """Get articles filtered by source name."""
        articles = [a for a in self._store.values() if a.get("source_name") == source_name]
        return Result.success(articles[:limit])


class InMemorySourceReadModel:
    """InMemory implementation of SourceReadModel port.

    Stores sources in a ``dict[str, dict]`` keyed by source_name.
    Data can be injected at construction time for test setup.

    Usage::

        sources = {"reuters": {"name": "reuters", "quality": 0.9}}
        model = InMemorySourceReadModel(sources=sources)
        result = model.get_source("reuters")
        assert result.is_success
    """

    def __init__(self, sources: dict[str, dict] | None = None) -> None:
        self._store = sources or {}

    def get_source(self, source_name: str) -> Result[dict]:
        """Get a single source by name."""
        if source_name not in self._store:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Source '{source_name}' not found",
                )
            )
        return Result.success(self._store[source_name])

    def get_all_sources(self) -> Result[list[dict]]:
        """Get all registered sources."""
        return Result.success(list(self._store.values()))


class InMemoryTopicReadModel:
    """InMemory implementation of TopicReadModel port.

    Stores topics in a ``dict[str, dict]`` keyed by topic_id.
    Data can be injected at construction time for test setup.

    Usage::

        topics = {"t1": {"id": "t1", "title": "...", "score": 0.85}}
        model = InMemoryTopicReadModel(topics=topics)
        result = model.get_topic("t1")
        assert result.is_success
    """

    def __init__(self, topics: dict[str, dict] | None = None) -> None:
        self._store = topics or {}

    def get_topic(self, topic_id: str) -> Result[dict]:
        """Get a single topic by ID."""
        if topic_id not in self._store:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Topic '{topic_id}' not found",
                )
            )
        return Result.success(self._store[topic_id])

    def get_topic_score(self, topic_id: str) -> Result[float]:
        """Get the current score for a topic."""
        if topic_id not in self._store:
            return Result.failure(
                Error(
                    code=ErrorCode.UNKNOWN,
                    message=f"Topic '{topic_id}' not found",
                )
            )
        return Result.success(self._store[topic_id].get("score", 0.0))
