"""
Language Value Object — Código de idioma ISO 639-1.

Representa un código de idioma de 2 letras según ISO 639-1.
Incluye validación contra lista de códigos permitidos y métodos
de utilidad como ``display_name()`` e ``is_rtl()``.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidLanguageError

# Códigos ISO 639-1 permitidos
_ALLOWED_CODES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
    "ar": "Arabic",
}

# Códigos RTL (right-to-left)
_RTL_CODES: set[str] = {"ar"}


@dataclass(frozen=True)
class Language(ValueObject):
    """Código de idioma ISO 639-1.

    Attributes:
        code: Código de 2 letras ISO 639-1. Se normaliza a lowercase.

    Raises:
        InvalidLanguageError: Si el código no es un ISO 639-1 válido
            o no está permitido.
    """

    code: str

    def __post_init__(self) -> None:
        """Validar y normalizar el código en construcción."""
        normalized = self.code.strip().lower()

        if len(normalized) != 2:
            raise InvalidLanguageError(
                f"Language code must be exactly 2 letters (ISO 639-1), "
                f"got '{self.code}'"
            )

        if not normalized.isalpha():
            raise InvalidLanguageError(
                f"Language code must contain only letters, got '{self.code}'"
            )

        if normalized not in _ALLOWED_CODES:
            raise InvalidLanguageError(
                f"Language code '{self.code}' is not in the allowed list: "
                f"{', '.join(sorted(_ALLOWED_CODES))}"
            )

        # Normalizar a lowercase si es necesario
        if self.code != normalized:
            object.__setattr__(self, "code", normalized)

    def display_name(self) -> str:
        """Retorna el nombre legible del idioma.

        Returns:
            Nombre del idioma (ej: "English", "Spanish").
        """
        return _ALLOWED_CODES.get(self.code, self.code)

    def is_rtl(self) -> bool:
        """Indica si el idioma es right-to-left.

        Returns:
            True si el idioma se escribe de derecha a izquierda.
        """
        return self.code in _RTL_CODES
