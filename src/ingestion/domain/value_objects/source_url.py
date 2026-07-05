"""
SourceUrl Value Object — URL base de un NewsSource.

Encapsula y valida la URL base de una fuente externa de información.
Provee normalización y validación estricta de formato.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidSourceUrlError
from ingestion.domain.value_objects._url_base import validate_url


@dataclass(frozen=True)
class SourceUrl(ValueObject):
    """URL base de un NewsSource.

    Attributes:
        value: La URL como string.

    Raises:
        InvalidSourceUrlError: Si la URL no pasa las validaciones.
    """

    value: str

    def __post_init__(self) -> None:
        """Validar y normalizar la URL en construcción."""
        stripped = validate_url(
            self.value,
            error_cls=InvalidSourceUrlError,
            field_name="Source URL",
        )

        # SourceUrl-specific: no fragments allowed
        parsed = urlparse(stripped)
        if parsed.fragment:
            raise InvalidSourceUrlError(
                "Source URL must not contain fragments (#)"
            )

    def normalized(self) -> str:
        """Retorna la URL normalizada (scheme lowercase, sin trailing slash).

        Returns:
            URL normalizada como string.
        """
        parsed = urlparse(self.value.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") if parsed.path else ""
        if path == "":
            path = ""
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{scheme}://{netloc}{path}{query}"
