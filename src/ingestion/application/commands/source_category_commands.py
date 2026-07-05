"""
Source Category Commands — asignación de categorías y topics a NewsSource.

Commands:
    - AssignCategoryToSourceCommand: Asignar categoría a una fuente.
    - AssignTopicToSourceCommand: Asignar topic a una fuente.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssignCategoryToSourceCommand:
    """Asignar una categoría existente a un NewsSource.

    No valida existencia de la categoría (consistencia eventual).

    Attributes:
        source_id: ID del NewsSource.
        category_id: ID de la categoría a asignar.
    """

    source_id: str
    category_id: str


@dataclass(frozen=True)
class AssignTopicToSourceCommand:
    """Asignar un topic existente a un NewsSource.

    No valida existencia del topic (consistencia eventual).

    Attributes:
        source_id: ID del NewsSource.
        topic_id: ID del topic a asignar.
    """

    source_id: str
    topic_id: str
