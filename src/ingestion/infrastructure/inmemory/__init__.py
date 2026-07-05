"""In-memory implementations of Ingestion BC ports.

These implementations use only Python collections (dict, list, set) and are
intended for testing and development. They are NOT thread-safe and do NOT
persist data across process restarts.

Exports:
    - InMemoryNewsSourceRepository
    - InMemoryFeedRepository
    - InMemoryRawArticleRepository
    - InMemoryCategoryRepository
    - InMemoryTopicRepository
    - InMemoryUnitOfWork
    - InMemoryEventPublisher
"""

from ingestion.infrastructure.inmemory.event_publisher import (
    InMemoryEventPublisher,
)
from ingestion.infrastructure.inmemory.repositories import (
    InMemoryCategoryRepository,
    InMemoryFeedRepository,
    InMemoryNewsSourceRepository,
    InMemoryRawArticleRepository,
    InMemoryTopicRepository,
)
from ingestion.infrastructure.inmemory.unit_of_work import InMemoryUnitOfWork

__all__ = [
    "InMemoryCategoryRepository",
    "InMemoryEventPublisher",
    "InMemoryFeedRepository",
    "InMemoryNewsSourceRepository",
    "InMemoryRawArticleRepository",
    "InMemoryTopicRepository",
    "InMemoryUnitOfWork",
]
