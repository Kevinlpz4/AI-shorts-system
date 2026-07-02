"""
Foundation Error System — Jerarquía de excepciones base.

Exporta FoundationError, DomainError, ApplicationError, InfrastructureError.

Uso::

    from foundation.errors import FoundationError, DomainError
"""
from foundation.errors.base import (
    ApplicationError,
    DomainError,
    FoundationError,
    InfrastructureError,
)

__all__ = [
    "FoundationError",
    "DomainError",
    "ApplicationError",
    "InfrastructureError",
]
