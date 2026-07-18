"""
Cache Ports — Protocol definitions and InMemory implementations for caching.

Cache ports are Protocol-only for now. InMemory implementations
are provided for testing. Real implementations (Redis, etc.) will
be added when deploying to production.

Cache ports:
    - PredictionCache: cache for prediction results (default TTL: 5 min)
    - AnalyticsCache: cache for analytics aggregation results (default TTL: 10 min)
    - KnowledgeCache: cache for knowledge timeline queries (default TTL: 1 hour)
"""
from __future__ import annotations

from typing import Any, Protocol


class PredictionCache(Protocol):
    """Cache for prediction results.

    Predictions are expensive to compute. Caching avoids redundant
    computation when the same input features produce the same prediction.
    """

    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict, ttl_seconds: int = 300) -> None: ...
    def invalidate(self, key: str) -> None: ...
    def clear(self) -> None: ...


class AnalyticsCache(Protocol):
    """Cache for analytics aggregation results.

    Analytics queries aggregate large datasets. Caching avoids
    redundant aggregation when the underlying data hasn't changed.
    """

    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict, ttl_seconds: int = 600) -> None: ...
    def invalidate(self, key: str) -> None: ...
    def clear(self) -> None: ...


class KnowledgeCache(Protocol):
    """Cache for knowledge timeline queries.

    Knowledge timeline queries involve sorting and filtering snapshots.
    Caching avoids redundant computation for the same entity+metric.
    """

    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None: ...
    def invalidate(self, key: str) -> None: ...
    def clear(self) -> None: ...


class InMemoryPredictionCache:
    """InMemory implementation of PredictionCache for testing.

    Simple dict-based storage with no TTL enforcement.
    TTL parameter is accepted but ignored — InMemory is for tests only.

    Usage::

        cache = InMemoryPredictionCache()
        cache.set("pred:a1", {"score": 0.85})
        assert cache.get("pred:a1") == {"score": 0.85}
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        """Get a cached prediction by key."""
        return self._store.get(key)

    def set(self, key: str, value: dict, ttl_seconds: int = 300) -> None:
        """Cache a prediction result."""
        self._store[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a cached prediction."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all cached predictions."""
        self._store.clear()


class InMemoryAnalyticsCache:
    """InMemory implementation of AnalyticsCache for testing.

    Simple dict-based storage with no TTL enforcement.

    Usage::

        cache = InMemoryAnalyticsCache()
        cache.set("analytics:reuters", {"avg_score": 0.72})
        assert cache.get("analytics:reuters") == {"avg_score": 0.72}
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        """Get a cached analytics result by key."""
        return self._store.get(key)

    def set(self, key: str, value: dict, ttl_seconds: int = 600) -> None:
        """Cache an analytics aggregation result."""
        self._store[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a cached analytics result."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all cached analytics results."""
        self._store.clear()


class InMemoryKnowledgeCache:
    """InMemory implementation of KnowledgeCache for testing.

    Simple dict-based storage with no TTL enforcement.
    Stores Any values since knowledge timeline data varies in type.

    Usage::

        cache = InMemoryKnowledgeCache()
        cache.set("timeline:reuters:approval_rate", evolution)
        assert cache.get("timeline:reuters:approval_rate") is not None
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        """Get a cached knowledge result by key."""
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Cache a knowledge timeline query result."""
        self._store[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a cached knowledge result."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all cached knowledge results."""
        self._store.clear()
