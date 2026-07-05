"""
CategoryName Value Object — Nombre legible de una categoría.

Encapsula y valida el nombre de una categoría temática.
Permite solo caracteres alfanuméricos, espacios, guiones y guiones bajos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidCategoryError

_MAX_LENGTH = 100
# Solo letras, espacios, números, guiones y guiones bajos
_VALID_PATTERN = re.compile(r"^[a-zA-Z0-9 _-]+$")


@dataclass(frozen=True)
class CategoryName(ValueObject):
    """Nombre legible de una categoría.

    Attributes:
        value: El nombre como string. Se auto-trim al construir.

    Raises:
        InvalidCategoryError: Si el nombre no pasa las validaciones.
    """

    value: str

    def __post_init__(self) -> None:
        """Validar y normalizar el nombre en construcción."""
        trimmed = self.value.strip()

        # No vacío después de trim
        if not trimmed:
            raise InvalidCategoryError("Category name must not be empty")

        # Longitud máxima
        if len(trimmed) > _MAX_LENGTH:
            raise InvalidCategoryError(
                f"Category name must not exceed {_MAX_LENGTH} characters, "
                f"got {len(trimmed)}"
            )

        # Solo caracteres permitidos
        if not _VALID_PATTERN.match(trimmed):
            raise InvalidCategoryError(
                "Category name must contain only letters, numbers, spaces, "
                "hyphens, and underscores"
            )

        # Auto-trim
        if self.value != trimmed:
            object.__setattr__(self, "value", trimmed)
