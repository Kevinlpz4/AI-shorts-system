"""
ArticleTitle Value Object — Título de un artículo.

Encapsula y valida el título de un artículo crudo obtenido de un Feed.
Incluye validación de longitud, caracteres de control y trim automático.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidArticleTitleError

# Caracteres de control (incluye \n, \r, \t)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

MAX_TITLE_LENGTH = 500


@dataclass(frozen=True)
class ArticleTitle(ValueObject):
    """Título de un artículo.

    Attributes:
        value: El título como string. Se auto-trim al construir.

    Raises:
        InvalidArticleTitleError: Si el título no pasa las validaciones.
    """

    value: str

    def __post_init__(self) -> None:
        """Validar y sanitizar el título en construcción."""
        trimmed = self.value.strip()
        self._validate_not_empty(trimmed)
        self._validate_max_length(trimmed)
        self._validate_no_control_chars(trimmed)
        self._apply_trim(trimmed)

    def _validate_not_empty(self, trimmed: str) -> None:
        """Validate that the title is not empty after trimming."""
        if not trimmed:
            raise InvalidArticleTitleError("Article title must not be empty")

    def _validate_max_length(self, trimmed: str) -> None:
        """Validate that the title does not exceed max length."""
        if len(trimmed) > MAX_TITLE_LENGTH:
            raise InvalidArticleTitleError(
                f"Article title must not exceed {MAX_TITLE_LENGTH} characters, "
                f"got {len(trimmed)}"
            )

    def _validate_no_control_chars(self, trimmed: str) -> None:
        """Validate that the title contains no control characters."""
        if _CONTROL_CHARS_RE.search(trimmed):
            raise InvalidArticleTitleError(
                "Article title must not contain control characters"
            )

    def _apply_trim(self, trimmed: str) -> None:
        """Apply auto-trim using object.__setattr__ for frozen fields."""
        if self.value != trimmed:
            object.__setattr__(self, "value", trimmed)
