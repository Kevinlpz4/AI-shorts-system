"""
Category Entity — Clasificación temática con jerarquía opcional.

Category es una Entity (NO Aggregate Root). Tiene identidad y ciclo de vida,
pero no tiene entidades dependientes que requieran consistencia transaccional.
Es referenciada por ID desde NewsSource y Feed.

Invariantes:
  - I-18: slug MUST be unique across all categories (enforced by repository)
  - I-19: parent_id MUST NOT equal id (no self-parent)
  - I-20: Hierarchy MUST NOT contain cycles
  - I-21: Deactivating a category with active subcategories MUST cascade
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.base.entity import Entity

from ingestion.domain.entities.ids import CategoryId
from ingestion.domain.exceptions import InvalidCategoryError
from ingestion.domain.value_objects.category_name import CategoryName


@dataclass(eq=False)
class Category(Entity):
    """Clasificación temática con jerarquía opcional.

    Attributes:
        id: Identidad única de la categoría.
        name: Nombre legible validado por CategoryName VO.
        slug: Slug URL-friendly, único globalmente.
        parent_id: Referencia opcional a categoría padre.
        is_active: Si está habilitada.
    """

    id: CategoryId
    name: CategoryName
    slug: str
    parent_id: CategoryId | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validar invariantes en construcción."""
        if self.parent_id is not None and self.parent_id == self.id:
            raise InvalidCategoryError(
                "A category cannot be its own parent (I-19)"
            )

    def activate(self) -> None:
        """Marca la categoría como activa."""
        self.is_active = True

    def deactivate(self) -> None:
        """
        Marca la categoría como inactiva.

        NOTA: La validación de cascade a subcategorías activas (I-21) NO se
        implementa en esta entidad porque requiere consultar el repositorio
        (find_by_parent). Esto es una regla de Application Layer.
        """
        self.is_active = False

    def change_parent(self, new_parent: CategoryId | None) -> None:
        """Cambia la categoría padre.

        Valida:
          - No auto-referencia (I-19)
          - No ciclos (I-20)

        NOTA: La validación de ciclos (I-20) requiere acceso al repositorio
        para recorrer la jerarquía, lo cual NO puede hacerse dentro de la
        entidad. Se documenta para Application Layer.

        Args:
            new_parent: Nuevo CategoryId padre, o None para raíz.

        Raises:
            InvalidCategoryError: Si new_parent es la misma categoría.
        """
        if new_parent is not None and new_parent == self.id:
            raise InvalidCategoryError(
                "A category cannot be its own parent (I-19)"
            )
        self.parent_id = new_parent
