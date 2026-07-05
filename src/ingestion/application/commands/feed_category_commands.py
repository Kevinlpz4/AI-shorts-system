"""
Feed Category Commands — asignación de categorías y topics a Feed.

Commands:
    - AssignCategoryToFeedCommand: Asignar categoría a un feed.
    - AssignTopicToFeedCommand: Asignar topic a un feed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssignCategoryToFeedCommand:
    """Asignar una categoría existente a un Feed.

    No valida existencia de la categoría (consistencia eventual).

    Attributes:
        feed_id: ID del Feed.
        category_id: ID de la categoría a asignar.
    """

    feed_id: str
    category_id: str


@dataclass(frozen=True)
class AssignTopicToFeedCommand:
    """Asignar un topic existente a un Feed.

    No valida existencia del topic (consistencia eventual).

    Attributes:
        feed_id: ID del Feed.
        topic_id: ID del topic a asignar.
    """

    feed_id: str
    topic_id: str
