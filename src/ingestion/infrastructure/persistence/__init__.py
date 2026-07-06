"""Persistence infrastructure for the Ingestion Bounded Context.

This package provides the SQLAlchemy-based persistence layer. All reusable
components (base, engine, types, exceptions) are designed to be extractable
to a shared infrastructure package should a second Bounded Context need them.

Current scope (Sprint 5.1 - Sprint 5.4A):
    - ``PersistenceBase`` — DeclarativeBase with strict naming conventions
    - ``create_engine`` / ``create_session_factory`` — Engine and session lifecycle
    - ``EntityIdType[T]`` — Generic TypeDecorator for any ``EntityId`` subclass
    - ``PersistenceError`` hierarchy — Infrastructure exception base
    - ``IngestionSettings`` — Pydantic-based configuration
    - VO TypeDecorators (ArticleTitleType, ArticleUrlType, ...)
    - ORM Models (NewsSourceModel, FeedModel, RawArticleModel, CategoryModel, TopicModel)
    - Association Tables (news_source_category_table, ...)
    - ``SQLAlchemyUnitOfWork`` — Unit of Work con Session lifecycle

Public API
----------
>>> from ingestion.infrastructure.persistence import (
...     PersistenceBase,
...     create_engine,
...     create_session_factory,
...     EntityIdType,
...     PersistenceError,
...     IngestionSettings,
...     ArticleTitleType,
...     ArticleUrlType,
...     NewsSourceModel,
...     FeedModel,
... )
"""

from __future__ import annotations

from ingestion.infrastructure.persistence.base import PersistenceBase, naming_convention
from ingestion.infrastructure.persistence.config import IngestionSettings
from ingestion.infrastructure.persistence.decorators import (
    ArticleTitleType,
    ArticleUrlType,
    CategoryNameType,
    LanguageType,
    SourceTypeType,
    SourceUrlType,
    SyncModeType,
)
from ingestion.infrastructure.persistence.engine import create_engine, create_session_factory
from ingestion.infrastructure.persistence.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    PersistenceError,
)
from ingestion.infrastructure.persistence.models import (
    CategoryModel,
    FeedModel,
    NewsSourceModel,
    RawArticleModel,
    TopicModel,
    feed_category_table,
    feed_topic_table,
    news_source_category_table,
    news_source_topic_table,
)
from ingestion.infrastructure.persistence.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyFeedRepository,
    SQLAlchemyNewsSourceRepository,
    SQLAlchemyRawArticleRepository,
    SQLAlchemyTopicRepository,
)
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from ingestion.infrastructure.persistence.types import EntityIdType

__all__ = [
    # Base
    "PersistenceBase",
    "naming_convention",
    # Config
    "IngestionSettings",
    # Engine / Session
    "create_engine",
    "create_session_factory",
    # Exceptions
    "PersistenceError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    # TypeDecorators
    "EntityIdType",
    "ArticleTitleType",
    "ArticleUrlType",
    "CategoryNameType",
    "LanguageType",
    "SourceTypeType",
    "SourceUrlType",
    "SyncModeType",
    # ORM Models
    "NewsSourceModel",
    "FeedModel",
    "RawArticleModel",
    "CategoryModel",
    "TopicModel",
    # Association Tables
    "news_source_category_table",
    "news_source_topic_table",
    "feed_category_table",
    "feed_topic_table",
    # SQLAlchemy Repositories
    "SQLAlchemyNewsSourceRepository",
    "SQLAlchemyFeedRepository",
    "SQLAlchemyRawArticleRepository",
    "SQLAlchemyCategoryRepository",
    "SQLAlchemyTopicRepository",
    # Unit of Work
    "SQLAlchemyUnitOfWork",
]
