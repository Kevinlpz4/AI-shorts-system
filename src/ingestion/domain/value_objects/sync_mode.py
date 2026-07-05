"""
SyncMode Enum — Modo de sincronización para un Feed.

Define cómo se obtienen los datos de un Feed:
  - PULL: El sistema consulta periódicamente al Source.
  - PUSH: El Source notifica al sistema mediante webhook.
  - STREAM: Conexión persistente con el Source.
  - MANUAL: Solo se ejecuta bajo demanda explícita.
"""

from __future__ import annotations

from enum import Enum


class SyncMode(str, Enum):
    """Modo de sincronización de un Feed."""

    PULL = "PULL"
    PUSH = "PUSH"
    STREAM = "STREAM"
    MANUAL = "MANUAL"
