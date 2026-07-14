"""
Category Commands — operaciones CRUD y estado para Category.

Commands:
    - CreateCategoryCommand: Crear nueva categoría.
    - UpdateCategoryCommand: Actualizar categoría existente.
    - ActivateCategoryCommand: Activar categoría.
    - DeactivateCategoryCommand: Desactivar categoría.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateCategoryCommand:
    """Crear una nueva Category.

    Attributes:
        name: Nombre legible de la categoría.
        slug: Slug URL-friendly, único globalmente.
        parent_id: ID de la categoría padre (opcional).
    """

    name: str
    slug: str
    parent_id: str | None = None


@dataclass(frozen=True)
class UpdateCategoryCommand:
    """Actualizar una Category existente.

    Todos los campos excepto ``category_id`` son opcionales.
    Solo se actualizan los campos provistos (no None).

    Attributes:
        category_id: ID de la categoría a actualizar.
        name: Nuevo nombre (opcional).
        slug: Nuevo slug (opcional).
        parent_id: Nuevo padre (opcional).
    """

    category_id: str
    name: str | None = None
    slug: str | None = None
    parent_id: str | None = None


@dataclass(frozen=True)
class ActivateCategoryCommand:
    """Activar una Category.

    Attributes:
        category_id: ID de la categoría a activar.
    """

    category_id: str


@dataclass(frozen=True)
class DeactivateCategoryCommand:
    """Desactivar una Category.

    Attributes:
        category_id: ID de la categoría a desactivar.
    """

    category_id: str
