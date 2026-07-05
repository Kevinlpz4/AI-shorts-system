"""
Common types for the Application Layer.

Exporta QueryResult y PaginatedDTO.

Uso::

    from ingestion.application.common import PaginatedDTO, QueryResult
"""

from __future__ import annotations

from ingestion.application.common.paginated_dto import PaginatedDTO
from ingestion.application.common.query_result import QueryResult

__all__ = [
    "PaginatedDTO",
    "QueryResult",
]
