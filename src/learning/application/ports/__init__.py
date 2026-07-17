"""
Application Ports — Output ports for dependency inversion.

Estos Protocols definen los contratos que la capa de infraestructura
debe implementar. La capa de aplicación (services) depende de estos
Protocols, no de implementaciones concretas.

Ports:
    - UnitOfWork: Context manager para transacciones.
    - EventPublisher: Publicación de eventos de dominio.
    - ClockPort: Obtención de la hora actual del sistema.
    - DatasetExporter: Exportación de datasets de entrenamiento.
    - LearningEventPublisher: Publicación de eventos tipados del Learning BC.
"""

from __future__ import annotations

from learning.application.ports.clock import ClockPort
from learning.application.ports.dataset_exporter import DatasetExporter
from learning.application.ports.event_publisher import EventPublisher
from learning.application.ports.learning_event_publisher import LearningEventPublisher
from learning.application.ports.unit_of_work import UnitOfWork

__all__ = [
    "ClockPort",
    "DatasetExporter",
    "EventPublisher",
    "LearningEventPublisher",
    "UnitOfWork",
]
