"""
Foundation Layer — Base técnica compartida del sistema.

Este paquete contiene los mecanismos técnicos transversales que
todos los Bounded Contexts utilizan:

  - EntityId: Value Object base para IDs tipados
  - FoundationEncoder: JSONEncoder genérico para tipos Foundation
  - ValueObject: Marker class para Value Objects de dominio
  - Entity: Base class para Entidades de dominio (igualdad por identidad)
  - AggregateRoot: Base class para Aggregate Roots (Entity + eventos internos)
  - FoundationError: Base exception para TODAS las excepciones del sistema
  - DomainError: Excepción de dominio (reglas de negocio)
  - ApplicationError: Excepción de aplicación (comandos inválidos)
  - InfrastructureError: Excepción de infraestructura (DB, red, timeout)
  - Result[T]: Result Pattern para operaciones que pueden fallar
  - Error: Error de datos para Result.failure() (NO es excepción)
  - ErrorCode: Enum de códigos de error Foundation
  - DomainEvent: Base class para Domain Events intra-BC
  - IntegrationEvent: Base class para Integration Events entre BCs
  - ClockPort: Protocol de abstracción del tiempo
  - SystemClock: Clock real (datetime.now(timezone.utc))
  - FrozenClock: Clock congelado para tests (con advance())
  - UUIDProvider: Protocol de generación de UUIDs
  - SystemUUIDProvider: UUID real (uuid4())
  - SequentialUUIDProvider: UUID secuencial determinístico para tests

Principios:
  - Zero dependencias externas (stdlib-only)
  - Inmutabilidad por defecto
  - Fail fast en construcción

Ver docs/architecture/foundation-design.md para el diseño completo.
"""

from foundation.base.aggregate_root import AggregateRoot
from foundation.base.entity import Entity
from foundation.base.value_object import ValueObject
from foundation.entity_id import EntityId
from foundation.errors import ApplicationError, DomainError, FoundationError, InfrastructureError
from foundation.events.domain_event import DomainEvent
from foundation.events.integration_event import IntegrationEvent
from foundation.json_encoder import FoundationEncoder
from foundation.ports.clock import ClockPort, FrozenClock, SystemClock
from foundation.ports.uuid_provider import (
    SequentialUUIDProvider,
    SystemUUIDProvider,
    UUIDProvider,
)
from foundation.result.result import Error, ErrorCode, Failure, Result, Success

__all__ = [
    "AggregateRoot",
    "ApplicationError",
    "ClockPort",
    "DomainError",
    "DomainEvent",
    "Entity",
    "EntityId",
    "Error",
    "ErrorCode",
    "Failure",
    "FrozenClock",
    "FoundationEncoder",
    "FoundationError",
    "InfrastructureError",
    "IntegrationEvent",
    "Result",
    "SequentialUUIDProvider",
    "Success",
    "SystemClock",
    "SystemUUIDProvider",
    "UUIDProvider",
    "ValueObject",
]
