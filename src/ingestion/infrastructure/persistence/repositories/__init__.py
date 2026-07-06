"""
SQLAlchemy repository implementations for the Ingestion Bounded Context.

All repositories take a ``Session`` in ``__init__`` and implement the
corresponding ``Protocol`` from ``ingestion.domain.ports.repositories``.

Domain → ORM mapping is encapsulated entirely within each repository.
Application and Domain layers never know about ORM models.
"""

from __future__ import annotations

from ingestion.infrastructure.persistence.repositories.news_source import (
    SQLAlchemyNewsSourceRepository,
)
from ingestion.infrastructure.persistence.repositories.feed import (
    SQLAlchemyFeedRepository,
)
from ingestion.infrastructure.persistence.repositories.raw_article import (
    SQLAlchemyRawArticleRepository,
)
from ingestion.infrastructure.persistence.repositories.category import (
    SQLAlchemyCategoryRepository,
)
from ingestion.infrastructure.persistence.repositories.topic import (
    SQLAlchemyTopicRepository,
)

__all__ = [
    "SQLAlchemyNewsSourceRepository",
    "SQLAlchemyFeedRepository",
    "SQLAlchemyRawArticleRepository",
    "SQLAlchemyCategoryRepository",
    "SQLAlchemyTopicRepository",
]
