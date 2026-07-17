"""
Learning Application Layer — Core orchestrator of use cases.

Esta capa orquesta las operaciones del dominio (FeedbackRecord, LearningSignal,
LearningModel, SourceQuality) sin contener lógica de negocio.

Submódulos:
    - ``commands/`` — 7 commandos CQRS (data transport, frozen dataclasses).
    - ``queries/`` — 8 consultas CQRS (data transport, frozen dataclasses).
    - ``dto/`` — Data Transfer Objects inmutables (solo tipos primitivos).
    - ``mappers/`` — Conversión Domain Entity → DTO (sin lógica de negocio).
    - ``ports/`` — 5 output ports (UnitOfWork, EventPublisher, ClockPort,
      DatasetExporter, LearningEventPublisher).
    - ``exceptions/`` — Jerarquía de excepciones de aplicación.
    - ``errors/`` — ErrorMapper (DomainError → Error con ApplicationErrorCode).
    - ``common/`` — Tipos compartidos (QueryResult, PaginatedDTO).

Dependencias:
    - ``learning.domain`` (FROZEN) — entidades, VOs, eventos, repositorios
    - ``foundation`` (FROZEN) — Result, Error, EventBus, ports

NO depende de:
    - infrastructure/ (se inyecta vía ports)
    - presentation/ (la capa superior)

Uso::

    from learning.application import QueryResult, PaginatedDTO
    from learning.application.commands import RecordFeedbackCommand
    from learning.application.queries import GetFeedbackQuery
    from learning.application.dto import FeedbackSummaryDTO
    from learning.application.mappers import FeedbackMapper
    from learning.application.ports import UnitOfWork, EventPublisher
    from learning.application.errors import ErrorMapper
    from learning.application.exceptions import ApplicationErrorCode
    from learning.application.common import PaginatedDTO
"""

from __future__ import annotations

from learning.application.common import PaginatedDTO, QueryResult

__all__ = [
    "PaginatedDTO",
    "QueryResult",
]
