"""
Ingestion Events — integration events FROM Ingestion BC that Learning consumes.

Each event carries serializable data only — NO domain objects from Ingestion.
All events inherit from foundation.events.integration_event.IntegrationEvent.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from foundation.events.integration_event import IntegrationEvent


@dataclass(frozen=True)
class RawArticleCollected(IntegrationEvent):
    """Ingestion collected a new raw article.

    Signals that a new raw article has been collected from a source.
    Learning can use this to register signals or trigger predictions.
    """

    source_boundary: str = "ingestion"
    article_id: str = ""
    source_name: str = ""
    title: str = ""
    url: str = ""
    collected_at: str = ""  # ISO format


@dataclass(frozen=True)
class RawArticleRejected(IntegrationEvent):
    """Ingestion rejected a raw article.

    Signals that an article was rejected during ingestion processing.
    Learning can use this to update source quality profiles.
    """

    source_boundary: str = "ingestion"
    article_id: str = ""
    source_name: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SourceRegistered(IntegrationEvent):
    """A new source was registered in Ingestion.

    Signals that a new content source was added to the system.
    Learning can use this to initialize source quality tracking.
    """

    source_boundary: str = "ingestion"
    source_id: str = ""
    source_name: str = ""
    source_type: str = ""


@dataclass(frozen=True)
class FeedRegistered(IntegrationEvent):
    """A new feed was registered in Ingestion.

    Signals that a new RSS/web feed was added to a source.
    Learning can use this for source-level analytics.
    """

    source_boundary: str = "ingestion"
    feed_id: str = ""
    source_id: str = ""
    feed_url: str = ""


@dataclass(frozen=True)
class ArticleCreated(IntegrationEvent):
    """A processed article was created.

    Signals that an article completed ingestion processing and is now
    available as a processed article. Learning can use this to register
    signals and generate recommendations.
    """

    source_boundary: str = "ingestion"
    article_id: str = ""
    source_name: str = ""
    title: str = ""
    content_preview: str = ""
