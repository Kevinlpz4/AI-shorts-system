"""
Script DTOs — Data Transfer Objects for Script module
=======================================================
DTOs de entrada/salida para los casos de uso de Script.

Propósito:
  - Aislar la capa de presentación del dominio
  - Definir contratos claros de entrada/salida
  - Solo contienen datos, sin comportamiento
"""

from dataclasses import dataclass, field
from typing import Optional

from domain.entities.script import Script


@dataclass
class ScriptDTO:
    """
    DTO de salida: representación pública de un Script.

    No expone la entidad de dominio directamente.
    Calcula word_count e is_valid a partir de los datos.

    Atributos:
        id: ID único del script.
        topic_id: FK al ResearchTopic.
        hook: Gancho inicial.
        body: Cuerpo del guion.
        cta: Call-to-action.
        duration: Duración en segundos.
        tone: Tono del guion.
        format: Formato del guion.
        word_count: Cantidad de palabras.
        is_valid: Si pasa las validaciones de calidad.
        created_at: Fecha de creación ISO.
        updated_at: Fecha de última modificación ISO.
    """
    id: str
    topic_id: str
    hook: str
    body: str
    cta: str
    duration: int
    tone: str
    format: str
    word_count: int
    is_valid: bool
    created_at: str
    updated_at: str

    @staticmethod
    def from_entity(script: Script) -> "ScriptDTO":
        """
        Convierte una entidad Script → ScriptDTO.

        Es una función pura: mismo input → mismo output.
        No modifica la entidad.
        """
        return ScriptDTO(
            id=script.id,
            topic_id=script.topic_id,
            hook=script.hook,
            body=script.body,
            cta=script.cta,
            duration=int(script.duration),
            tone=script.tone,
            format=script.format,
            word_count=script.word_count,
            is_valid=script.is_valid(),
            created_at=script.created_at,
            updated_at=script.updated_at,
        )


@dataclass
class GenerateScriptRequest:
    """
    DTO de entrada: solicitud para generar un guion.

    Atributos:
        topic_id: ID del ResearchTopic aprobado.
        duration: Duración objetivo en segundos (default 45).
        tone: Tono del guion (default "educational").
    """
    topic_id: str
    duration: int = 45
    tone: str = "educational"
