"""
Ingestion Application Layer — Core orchestrator of use cases.

Esta capa orquesta las operaciones del dominio (NewsSource, Feed, RawArticle)
sin contener lógica de negocio. Implementa los 21 use cases del BC Ingestion
agrupados en 3 servicios: SourceService, FeedService, ArticleService.

Submódulos:
    - ``commands/`` — 15 comandos CQRS (@dataclass frozen, sin lógica).
    - ``queries/`` — 6 consultas CQRS (@dataclass frozen, sin lógica).
    - ``dto/`` — 10 Data Transfer Objects inmutables.
    - ``mappers/`` — 5 mappers (domain entity → DTO).
    - ``errors/`` — ErrorMapper (DomainError → Error con ApplicationErrorCode).
    - ``exceptions/`` — Jerarquía de excepciones de aplicación.
    - ``common/`` — Tipos compartidos (QueryResult, PaginatedDTO).

Dependencias:
    - ``ingestion.domain`` (FROZEN) — entidades, VOs, eventos, repositorios
    - ``foundation`` (FROZEN) — Result, Error, EventBus, ports

NO depende de:
    - infrastructure/ (se inyecta vía ports)
    - presentation/ (la capa superior)

Uso::

    from ingestion.application import QueryResult
    from ingestion.application.commands import RegisterSourceCommand
    from ingestion.application.queries import FindSourceQuery
    from ingestion.application.dto import SourceSummaryDTO
    from ingestion.application.mappers import SourceMapper
    from ingestion.application.errors import ErrorMapper
    from ingestion.application.exceptions import ApplicationErrorCode
    from ingestion.application.common import PaginatedDTO
"""

from __future__ import annotations

from ingestion.application.common import PaginatedDTO, QueryResult

__all__ = [
    "PaginatedDTO",
    "QueryResult",
]
