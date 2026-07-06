"""
SQLAlchemy TypeDecorators for Ingestion Domain Value Objects.

Each Value Object gets its own TypeDecorator following the pattern:

    process_bind_param:  VO | None → str | None
    process_result_value: str | None → VO | None

This provides:
  - Type safety: ORM columns have domain types, not raw strings
  - Deep defense: VO validation runs when loading from DB
  - Encapsulation: conversion logic in one place, not scattered in repositories

Current decorators
------------------
* ``ArticleTitleType`` — maps ``ArticleTitle`` ↔ ``VARCHAR(500)``
* ``ArticleUrlType`` — maps ``ArticleUrl`` ↔ ``VARCHAR(2048)``
* ``CategoryNameType`` — maps ``CategoryName`` ↔ ``VARCHAR(100)``
* ``SourceUrlType`` — maps ``SourceUrl`` ↔ ``VARCHAR(2048)``
* ``LanguageType`` — maps ``Language`` ↔ ``VARCHAR(2)``
* ``SourceTypeType`` — maps ``SourceType`` (enum) ↔ ``VARCHAR(20)``
* ``SyncModeType`` — maps ``SyncMode`` (enum) ↔ ``VARCHAR(20)``

Usage::

    from ingestion.infrastructure.persistence.decorators import (
        ArticleTitleType, ArticleUrlType, CategoryNameType,
        SourceUrlType, LanguageType, SourceTypeType, SyncModeType,
    )

    class FeedModel(PersistenceBase):
        label: Mapped[ArticleTitle] = mapped_column(ArticleTitleType, ...)
        url: Mapped[ArticleUrl] = mapped_column(ArticleUrlType, ...)
"""

from __future__ import annotations

from sqlalchemy.types import String, TypeDecorator

from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode

# ══════════════════════════════════════════════════════════════════════════════
# Value Object TypeDecorators (T-02)
# ══════════════════════════════════════════════════════════════════════════════


class ArticleTitleType(TypeDecorator):
    """TypeDecorator for ``ArticleTitle`` ↔ ``VARCHAR(500)``.

    ``ArticleTitle`` wraps a ``str`` in its ``.value`` attribute.
    """

    impl = String(500)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: ArticleTitle | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> ArticleTitle | None:
        return ArticleTitle(value) if value is not None else None


class ArticleUrlType(TypeDecorator):
    """TypeDecorator for ``ArticleUrl`` ↔ ``VARCHAR(2048)``.

    ``ArticleUrl`` wraps a ``str`` in its ``.value`` attribute.
    """

    impl = String(2048)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: ArticleUrl | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> ArticleUrl | None:
        return ArticleUrl(value) if value is not None else None


class CategoryNameType(TypeDecorator):
    """TypeDecorator for ``CategoryName`` ↔ ``VARCHAR(100)``.

    ``CategoryName`` wraps a ``str`` in its ``.value`` attribute.
    """

    impl = String(100)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: CategoryName | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> CategoryName | None:
        return CategoryName(value) if value is not None else None


class SourceUrlType(TypeDecorator):
    """TypeDecorator for ``SourceUrl`` ↔ ``VARCHAR(2048)``.

    ``SourceUrl`` wraps a ``str`` in its ``.value`` attribute.
    """

    impl = String(2048)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: SourceUrl | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> SourceUrl | None:
        return SourceUrl(value) if value is not None else None


class LanguageType(TypeDecorator):
    """TypeDecorator for ``Language`` ↔ ``VARCHAR(2)``.

    **IMPORTANT**: ``Language`` uses ``.code`` (not ``.value``) as its
    internal attribute. This is the ONLY VO with a non-standard attribute
    name.
    """

    impl = String(2)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: Language | None,
        dialect: object,
    ) -> str | None:
        return value.code if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> Language | None:
        return Language(value) if value is not None else None


# ══════════════════════════════════════════════════════════════════════════════
# Enum TypeDecorators (T-03)
# ══════════════════════════════════════════════════════════════════════════════


class SourceTypeType(TypeDecorator):
    """TypeDecorator for ``SourceType`` enum ↔ ``VARCHAR(20)``.

    Stored as VARCHAR for portability (SQLite compat). The enum's ``.value``
    is the string representation.
    """

    impl = String(20)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: SourceType | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> SourceType | None:
        return SourceType(value) if value is not None else None


class SyncModeType(TypeDecorator):
    """TypeDecorator for ``SyncMode`` enum ↔ ``VARCHAR(20)``.

    Stored as VARCHAR for portability (SQLite compat).
    """

    impl = String(20)
    cache_ok = True

    def process_bind_param(  # type: ignore[override]
        self,
        value: SyncMode | None,
        dialect: object,
    ) -> str | None:
        return value.value if value is not None else None

    def process_result_value(  # type: ignore[override]
        self,
        value: str | None,
        dialect: object,
    ) -> SyncMode | None:
        return SyncMode(value) if value is not None else None


__all__ = [
    "ArticleTitleType",
    "ArticleUrlType",
    "CategoryNameType",
    "SourceUrlType",
    "LanguageType",
    "SourceTypeType",
    "SyncModeType",
]
