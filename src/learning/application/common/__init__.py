"""
Common types for the Application Layer.

Exporta QueryResult y PaginatedDTO.

Uso::

    from learning.application.common import PaginatedDTO, QueryResult
"""

from __future__ import annotations

from learning.application.common.paginated_dto import PaginatedDTO
from learning.application.common.query_result import QueryResult

__all__ = [
    "PaginatedDTO",
    "QueryResult",
]
