"""
Private ``_Categorizable`` mixin — shared category/topic management.

Internal to the domain layer. NOT exported from the entities package.

Extracts the identical ``assign_category``, ``remove_category``,
``assign_topic``, ``remove_topic`` methods that were duplicated in
both ``NewsSource`` and ``Feed``.

Usage::

    class NewsSource(AggregateRoot, _Categorizable):
        def assign_category(self, category_id: CategoryId) -> None:
            self._assign_category(self.categories, category_id)

        def remove_category(self, category_id: CategoryId) -> None:
            self._remove_category(self.categories, category_id)
"""

from __future__ import annotations

from ingestion.domain.entities.ids import CategoryId, TopicId


class _Categorizable:
    """Mixin with category/topic management.

    Internal to domain — NOT exported. Both NewsSource and Feed use this
    to avoid duplicating the same four methods.

    NOTE: These methods silently ignore duplicates (assign) and
    non-existent items (remove), preserving the existing domain contract.
    Stricter validation can be added in Application Layer if needed.
    """

    def _assign_category(
        self, categories: list[CategoryId], category_id: CategoryId
    ) -> None:
        """Agrega una categoría si no está ya presente.

        Args:
            categories: The list to modify (in-place).
            category_id: Category to add.
        """
        if category_id not in categories:
            categories.append(category_id)

    def _remove_category(
        self, categories: list[CategoryId], category_id: CategoryId
    ) -> None:
        """Remueve una categoría si está presente.

        Args:
            categories: The list to modify (in-place).
            category_id: Category to remove.
        """
        if category_id in categories:
            categories.remove(category_id)

    def _assign_topic(
        self, topics: list[TopicId], topic_id: TopicId
    ) -> None:
        """Agrega un topic si no está ya presente.

        Args:
            topics: The list to modify (in-place).
            topic_id: Topic to add.
        """
        if topic_id not in topics:
            topics.append(topic_id)

    def _remove_topic(
        self, topics: list[TopicId], topic_id: TopicId
    ) -> None:
        """Remueve un topic si está presente.

        Args:
            topics: The list to modify (in-place).
            topic_id: Topic to remove.
        """
        if topic_id in topics:
            topics.remove(topic_id)
