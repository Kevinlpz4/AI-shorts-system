"""
Tests for Cache Protocol definitions and InMemory implementations.

Covers:
- InMemoryPredictionCache: set, get, invalidate, clear
- InMemoryAnalyticsCache: set, get, invalidate, clear
- InMemoryKnowledgeCache: set, get, invalidate, clear
"""
from __future__ import annotations

import pytest

from learning.infrastructure.caches import (
    InMemoryAnalyticsCache,
    InMemoryKnowledgeCache,
    InMemoryPredictionCache,
)


# ===========================================================================
# InMemoryPredictionCache
# ===========================================================================


class TestInMemoryPredictionCache:
    """Tests for InMemoryPredictionCache."""

    def test_set_and_get(self) -> None:
        """set stores a prediction dict, get retrieves it by key."""
        cache = InMemoryPredictionCache()
        data = {"score": 0.85, "confidence": 0.92}

        cache.set("pred:a1", data)

        assert cache.get("pred:a1") == data

    def test_get_not_found(self) -> None:
        """get returns None for a key that does not exist."""
        cache = InMemoryPredictionCache()
        assert cache.get("nonexistent") is None

    def test_invalidate(self) -> None:
        """invalidate removes a specific key from the cache."""
        cache = InMemoryPredictionCache()
        cache.set("pred:a1", {"score": 0.85})
        cache.set("pred:a2", {"score": 0.70})

        cache.invalidate("pred:a1")

        assert cache.get("pred:a1") is None
        assert cache.get("pred:a2") is not None

    def test_invalidate_nonexistent_key(self) -> None:
        """invalidate with a non-existent key does not raise."""
        cache = InMemoryPredictionCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self) -> None:
        """clear removes all entries from the cache."""
        cache = InMemoryPredictionCache()
        cache.set("pred:a1", {"score": 0.85})
        cache.set("pred:a2", {"score": 0.70})

        cache.clear()

        assert cache.get("pred:a1") is None
        assert cache.get("pred:a2") is None

    def test_set_overwrite(self) -> None:
        """set with existing key overwrites the value."""
        cache = InMemoryPredictionCache()
        cache.set("pred:a1", {"score": 0.5})
        cache.set("pred:a1", {"score": 0.9})

        assert cache.get("pred:a1") == {"score": 0.9}

    def test_ttl_accepted_but_ignored(self) -> None:
        """TTL parameter is accepted but not enforced (InMemory is for tests)."""
        cache = InMemoryPredictionCache()
        cache.set("pred:a1", {"score": 0.85}, ttl_seconds=1)
        # Still accessible — no TTL enforcement
        assert cache.get("pred:a1") == {"score": 0.85}


# ===========================================================================
# InMemoryAnalyticsCache
# ===========================================================================


class TestInMemoryAnalyticsCache:
    """Tests for InMemoryAnalyticsCache."""

    def test_set_and_get(self) -> None:
        """set stores an analytics dict, get retrieves it by key."""
        cache = InMemoryAnalyticsCache()
        data = {"avg_score": 0.72, "count": 150}

        cache.set("analytics:reuters", data)

        assert cache.get("analytics:reuters") == data

    def test_get_not_found(self) -> None:
        """get returns None for a key that does not exist."""
        cache = InMemoryAnalyticsCache()
        assert cache.get("nonexistent") is None

    def test_invalidate(self) -> None:
        """invalidate removes a specific key from the cache."""
        cache = InMemoryAnalyticsCache()
        cache.set("analytics:reuters", {"avg_score": 0.72})
        cache.set("analytics:bbc", {"avg_score": 0.65})

        cache.invalidate("analytics:reuters")

        assert cache.get("analytics:reuters") is None
        assert cache.get("analytics:bbc") is not None

    def test_invalidate_nonexistent_key(self) -> None:
        """invalidate with a non-existent key does not raise."""
        cache = InMemoryAnalyticsCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self) -> None:
        """clear removes all entries from the cache."""
        cache = InMemoryAnalyticsCache()
        cache.set("analytics:reuters", {"avg_score": 0.72})
        cache.set("analytics:bbc", {"avg_score": 0.65})

        cache.clear()

        assert cache.get("analytics:reuters") is None
        assert cache.get("analytics:bbc") is None


# ===========================================================================
# InMemoryKnowledgeCache
# ===========================================================================


class TestInMemoryKnowledgeCache:
    """Tests for InMemoryKnowledgeCache."""

    def test_set_and_get(self) -> None:
        """set stores an arbitrary value, get retrieves it by key."""
        cache = InMemoryKnowledgeCache()
        data = {"evolution": [0.5, 0.6, 0.7], "trend": "IMPROVING"}

        cache.set("timeline:reuters:approval_rate", data)

        assert cache.get("timeline:reuters:approval_rate") == data

    def test_get_not_found(self) -> None:
        """get returns None for a key that does not exist."""
        cache = InMemoryKnowledgeCache()
        assert cache.get("nonexistent") is None

    def test_invalidate(self) -> None:
        """invalidate removes a specific key from the cache."""
        cache = InMemoryKnowledgeCache()
        cache.set("timeline:reuters", {"value": 0.8})
        cache.set("timeline:bbc", {"value": 0.7})

        cache.invalidate("timeline:reuters")

        assert cache.get("timeline:reuters") is None
        assert cache.get("timeline:bbc") is not None

    def test_invalidate_nonexistent_key(self) -> None:
        """invalidate with a non-existent key does not raise."""
        cache = InMemoryKnowledgeCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self) -> None:
        """clear removes all entries from the cache."""
        cache = InMemoryKnowledgeCache()
        cache.set("timeline:reuters", {"value": 0.8})
        cache.set("timeline:bbc", {"value": 0.7})

        cache.clear()

        assert cache.get("timeline:reuters") is None
        assert cache.get("timeline:bbc") is None

    def test_set_any_value_type(self) -> None:
        """InMemoryKnowledgeCache accepts any value type (not just dicts)."""
        cache = InMemoryKnowledgeCache()
        cache.set("str_val", "hello")
        cache.set("list_val", [1, 2, 3])
        cache.set("int_val", 42)

        assert cache.get("str_val") == "hello"
        assert cache.get("list_val") == [1, 2, 3]
        assert cache.get("int_val") == 42
