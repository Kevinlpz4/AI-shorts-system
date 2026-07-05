"""
Application Ports — Output ports for dependency inversion.

Estos Protocols definen los contratos que la capa de infraestructura
debe implementar. La capa de aplicación (services) depende de estos
Protocols, no de implementaciones concretas.

Ports:
    - UnitOfWork: Context manager para transacciones.
    - EventPublisher: Publicación de eventos de dominio.
"""

from __future__ import annotations

from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.ports.unit_of_work import UnitOfWork

__all__ = [
    "EventPublisher",
    "UnitOfWork",
]
