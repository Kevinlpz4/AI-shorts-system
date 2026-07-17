"""
Source Commands — operaciones de actualización de perfiles de calidad de fuente.

Commands:
    - UpdateSourceProfileCommand: Actualizar el perfil de calidad de una fuente.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateSourceProfileCommand:
    """Actualizar el perfil de calidad de una fuente.

    Attributes:
        source_id: ID del SourceQualityProfile a actualizar.
        decision: Tipo de decisión a registrar (approved, rejected, etc.).
    """

    source_id: str
    decision: str
