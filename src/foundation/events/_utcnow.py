"""
Helper UTC timestamp para eventos.

Devuelve datetime actual en UTC (timezone-aware).
Privado del paquete ``events/`` — no se exporta en la API pública.
"""

from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Retorna datetime actual en UTC con timezone."""
    return datetime.now(timezone.utc)
