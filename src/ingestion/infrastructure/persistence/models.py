"""
ORM Models for the Ingestion Bounded Context.

This module contains the 5 model classes and 4 association tables that
implement the persistence design from ``persistence-design.md``.

Design principles
=================
1. **Models are NOT domain entities**. They are data-mapper representations.
2. **All relationships are ``viewonly=True``**. Domain aggregates control
   their own state; the ORM only reflects it.
3. **No ORM cascade for deletes**. ``ON DELETE`` is enforced at the DB level
   via DDL, preventing accidental mass-deletes from ORM operations.
4. **No Feed → RawArticles relationship**. RawArticle access is always
   paginated via repository.

Usage::

    from ingestion.infrastructure.persistence.models import (
        NewsSourceModel, FeedModel, RawArticleModel,
        CategoryModel, TopicModel,
    )

See Also
--------
* ``persistence-design.md`` — full schema, constraints, index specifications
* ``orm-mapping-strategy.md`` — relationship config, loading strategy, cascades
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    desc,
    func,
)
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    RawArticleId,
    SourceId,
    TopicId,
)
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy
from ingestion.infrastructure.persistence.base import PersistenceBase
from ingestion.infrastructure.persistence.decorators import (
    ArticleTitleType,
    ArticleUrlType,
    CategoryNameType,
    LanguageType,
    SourceTypeType,
    SourceUrlType,
    SyncModeType,
)
from ingestion.infrastructure.persistence.types import EntityIdType

# ══════════════════════════════════════════════════════════════════════════════
# Association Tables (M:N)
# ══════════════════════════════════════════════════════════════════════════════
# Using ``Table`` (not model classes) for pure FK-pair associations.
# YAGNI — add columns (assigned_at, assigned_by) only when needed.

news_source_category_table = Table(
    "ingestion_news_source_categories",
    PersistenceBase.metadata,
    Column("source_id", EntityIdType(SourceId),
           ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
           primary_key=True),
    Column("category_id", EntityIdType(CategoryId),
           ForeignKey("ingestion_categories.id", ondelete="CASCADE"),
           primary_key=True),
    Index("ix_nsc_category", "category_id"),
)

news_source_topic_table = Table(
    "ingestion_news_source_topics",
    PersistenceBase.metadata,
    Column("source_id", EntityIdType(SourceId),
           ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
           primary_key=True),
    Column("topic_id", EntityIdType(TopicId),
           ForeignKey("ingestion_topics.id", ondelete="CASCADE"),
           primary_key=True),
    Index("ix_nst_topic", "topic_id"),
)

feed_category_table = Table(
    "ingestion_feed_categories",
    PersistenceBase.metadata,
    Column("feed_id", EntityIdType(FeedId),
           ForeignKey("ingestion_feeds.id", ondelete="CASCADE"),
           primary_key=True),
    Column("category_id", EntityIdType(CategoryId),
           ForeignKey("ingestion_categories.id", ondelete="CASCADE"),
           primary_key=True),
    Index("ix_fc_category", "category_id"),
)

feed_topic_table = Table(
    "ingestion_feed_topics",
    PersistenceBase.metadata,
    Column("feed_id", EntityIdType(FeedId),
           ForeignKey("ingestion_feeds.id", ondelete="CASCADE"),
           primary_key=True),
    Column("topic_id", EntityIdType(TopicId),
           ForeignKey("ingestion_topics.id", ondelete="CASCADE"),
           primary_key=True),
    Index("ix_ft_topic", "topic_id"),
)

# ══════════════════════════════════════════════════════════════════════════════
# ORM Models
# ══════════════════════════════════════════════════════════════════════════════


class NewsSourceModel(PersistenceBase):
    """ORM model for the ``ingestion_news_sources`` table.

    Maps to the ``NewsSource`` aggregate root (SourceId, SourceType, SourceUrl).
    """

    __tablename__ = "ingestion_news_sources"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: Mapped[SourceId] = mapped_column(
        EntityIdType(SourceId), primary_key=True,
    )

    # ── Domain Attributes ──────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    source_type: Mapped[SourceType] = mapped_column(
        SourceTypeType, nullable=False,
    )
    source_url: Mapped[SourceUrl] = mapped_column(
        SourceUrlType, nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True,
    )

    # ── Optimistic Locking ─────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Audit Timestamps ──────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────

    # 1:N → Feeds (lazy, viewonly)
    feeds: Mapped[list[FeedModel]] = relationship(
        back_populates="source",
        lazy="select",
        cascade="save-update, merge",
        viewonly=True,
    )

    # M:N → Categories via association table
    categories: Mapped[list[CategoryModel]] = relationship(
        secondary=news_source_category_table,
        lazy="selectin",
        viewonly=True,
    )

    # M:N → Topics via association table
    topics: Mapped[list[TopicModel]] = relationship(
        secondary=news_source_topic_table,
        lazy="selectin",
        viewonly=True,
    )

    # ── Table args (version_id_col + indexes) ──────────────────────────────
    __mapper_args__ = {
        "version_id_col": version,
    }

    __table_args__ = (
        UniqueConstraint("name", name="uq_news_source_name"),
        Index("ix_news_sources_active", "is_active"),
    )


class FeedModel(PersistenceBase):
    """ORM model for the ``ingestion_feeds`` table.

    Maps to the ``Feed`` aggregate root. Includes composite mapping for
    ``SyncPolicy`` (7 columns → 1 VO).
    """

    __tablename__ = "ingestion_feeds"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: Mapped[FeedId] = mapped_column(
        EntityIdType(FeedId), primary_key=True,
    )

    # ── Foreign Keys ───────────────────────────────────────────────────────
    source_id: Mapped[SourceId] = mapped_column(
        EntityIdType(SourceId),
        ForeignKey("ingestion_news_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Domain Attributes ──────────────────────────────────────────────────
    url: Mapped[ArticleUrl] = mapped_column(
        ArticleUrlType, nullable=False,
    )
    label: Mapped[ArticleTitle] = mapped_column(
        ArticleTitleType, nullable=False,
    )
    language: Mapped[Language] = mapped_column(
        LanguageType, nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True,
    )

    # ── SyncPolicy (composite — 7 columns) ─────────────────────────────────
    sync_mode: Mapped[SyncMode] = mapped_column(
        SyncModeType, nullable=False, default=SyncMode.PULL,
    )
    interval_minutes: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    max_retries: Mapped[int] = mapped_column(
        nullable=False, default=3,
    )
    backoff_multiplier: Mapped[float] = mapped_column(
        nullable=False, default=2.0,
    )
    max_backoff_minutes: Mapped[int] = mapped_column(
        nullable=False, default=60,
    )
    timeout_seconds: Mapped[int] = mapped_column(
        nullable=False, default=30,
    )
    max_items_per_run: Mapped[int] = mapped_column(
        nullable=False, default=100,
    )

    # ── Composite SyncPolicy ──────────────────────────────────────────────
    # Order must match SyncPolicy.__init__:
    #   mode, interval_minutes, max_retries, backoff_multiplier,
    #   max_backoff_minutes, timeout_seconds, max_items_per_run
    sync_policy: Mapped[SyncPolicy] = composite(
        SyncPolicy,
        sync_mode,
        interval_minutes,
        max_retries,
        backoff_multiplier,
        max_backoff_minutes,
        timeout_seconds,
        max_items_per_run,
    )

    # ── Execution State ────────────────────────────────────────────────────
    retry_count: Mapped[int] = mapped_column(
        nullable=False, default=0,
    )

    # ── Optimistic Locking ─────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Audit Timestamps ──────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────

    # N:1 → NewsSource (joined, viewonly)
    source: Mapped[NewsSourceModel] = relationship(
        back_populates="feeds",
        lazy="joined",
        viewonly=True,
    )

    # M:N → Categories via association table
    categories: Mapped[list[CategoryModel]] = relationship(
        secondary=feed_category_table,
        lazy="selectin",
        viewonly=True,
    )

    # M:N → Topics via association table
    topics: Mapped[list[TopicModel]] = relationship(
        secondary=feed_topic_table,
        lazy="selectin",
        viewonly=True,
    )

    # ── Table args (version_id_col + indexes) ──────────────────────────────
    __mapper_args__ = {
        "version_id_col": version,
    }

    __table_args__ = (
        UniqueConstraint("source_id", "url", name="uq_feed_source_url"),
        Index("ix_feeds_source_active", "source_id", "is_active"),
    )


class RawArticleModel(PersistenceBase):
    """ORM model for the ``ingestion_raw_articles`` table.

    Maps to the ``RawArticle`` entity (immutable — no ``version``,
    no ``updated_at``).

    **NO relationship from Feed**: RawArticle access is always paginated
    via repository.
    """

    __tablename__ = "ingestion_raw_articles"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: Mapped[RawArticleId] = mapped_column(
        EntityIdType(RawArticleId), primary_key=True,
    )

    # ── Foreign Keys ───────────────────────────────────────────────────────
    feed_id: Mapped[FeedId] = mapped_column(
        EntityIdType(FeedId),
        ForeignKey("ingestion_feeds.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ── Domain Attributes ──────────────────────────────────────────────────
    external_id: Mapped[str] = mapped_column(
        String(512), nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )
    title: Mapped[ArticleTitle] = mapped_column(
        ArticleTitleType, nullable=False,
    )
    url: Mapped[ArticleUrl] = mapped_column(
        ArticleUrlType, nullable=False,
    )
    author: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )
    language: Mapped[Language | None] = mapped_column(
        LanguageType, nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    content_preview: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    # NOTE: ``metadata`` is reserved on ``DeclarativeBase`` (it's the MetaData
    # instance). Use ``provider_metadata`` as the Python attribute name and
    # map to the ``metadata`` database column explicitly.
    provider_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSON(none_as_null=False),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    # ── Audit Timestamp ────────────────────────────────────────────────────
    # RawArticle is IMMUTABLE — no version, no updated_at.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    # ── Table args (indexes only — no version_id_col) ──────────────────────
    __table_args__ = (
        UniqueConstraint("feed_id", "external_id", name="uq_raw_article_feed_external"),
        UniqueConstraint("feed_id", "content_hash", name="uq_raw_article_feed_hash"),
        CheckConstraint(
            "LENGTH(content_hash) = 64",
            name="ck_raw_article_hash_length",
        ),
        Index("ix_raw_articles_feed_fetched", "feed_id", desc("fetched_at")),
        Index("ix_raw_articles_feed_url", "feed_id", "url"),
    )


class CategoryModel(PersistenceBase):
    """ORM model for the ``ingestion_categories`` table.

    Maps to the ``Category`` entity with self-referencing hierarchy.
    Only the ``parent`` relationship is mapped (N:1). The children
    collection is accessed via repository.
    """

    __tablename__ = "ingestion_categories"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: Mapped[CategoryId] = mapped_column(
        EntityIdType(CategoryId), primary_key=True,
    )

    # ── Domain Attributes ──────────────────────────────────────────────────
    name: Mapped[CategoryName] = mapped_column(
        CategoryNameType, nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(150), nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True,
    )

    # ── Self-Referencing FK ────────────────────────────────────────────────
    parent_id: Mapped[CategoryId | None] = mapped_column(
        EntityIdType(CategoryId),
        ForeignKey("ingestion_categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Optimistic Locking ─────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Audit Timestamps ──────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )

    # ── Relationships ──────────────────────────────────────────────────────

    # Self-referencing parent (N:1) — joined load
    parent: Mapped[CategoryModel | None] = relationship(
        remote_side="CategoryModel.id",
        lazy="joined",
        viewonly=True,
    )

    # ── Table args (version_id_col + indexes) ──────────────────────────────
    __mapper_args__ = {
        "version_id_col": version,
    }

    __table_args__ = (
        UniqueConstraint("slug", name="uq_category_slug"),
        CheckConstraint(
            "id != parent_id",
            name="ck_category_no_self_parent",
        ),
        Index("ix_categories_parent", "parent_id"),
        Index("ix_categories_active", "is_active"),
    )


class TopicModel(PersistenceBase):
    """ORM model for the ``ingestion_topics`` table.

    Maps to the ``Topic`` entity — the simplest model in the schema.
    No VOs, no FKs, no hierarchy.
    """

    __tablename__ = "ingestion_topics"

    # ── Primary Key ────────────────────────────────────────────────────────
    id: Mapped[TopicId] = mapped_column(
        EntityIdType(TopicId), primary_key=True,
    )

    # ── Domain Attributes ──────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True,
    )

    # ── Optimistic Locking ─────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
    )

    # ── Audit Timestamps ──────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),
    )

    # ── Table args (version_id_col + indexes) ──────────────────────────────
    __mapper_args__ = {
        "version_id_col": version,
    }

    __table_args__ = (
        UniqueConstraint("name", name="uq_topic_name"),
        Index("ix_topics_active", "is_active"),
    )
