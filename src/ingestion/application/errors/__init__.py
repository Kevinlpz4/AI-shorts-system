"""
Application Error Mapping — convierte errores de dominio y Result
en errores de aplicación con ``ApplicationErrorCode``.

Exporta ``ErrorMapper``.

Uso::

    from ingestion.application.errors import ErrorMapper
"""
from __future__ import annotations

from ingestion.application.errors.error_mapper import ErrorMapper

__all__ = [
    "ErrorMapper",
]
