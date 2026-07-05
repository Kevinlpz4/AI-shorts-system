"""
Application Queries — 6 consultas CQRS para el BC Ingestion.

Cada query es un ``@dataclass(frozen=True)`` sin lógica ni validaciones.
Solo transporte de datos.

Uso::

    from ingestion.application.queries import (
        FindSourceQuery,
        ListActiveSourcesQuery,
    )
"""
from __future__ import annotations

from ingestion.application.queries.article_queries import (
    FindArticleQuery,
    ListArticlesQuery,
)
from ingestion.application.queries.feed_queries import FindFeedQuery, ListFeedsQuery
from ingestion.application.queries.source_queries import (
    FindSourceQuery,
    ListActiveSourcesQuery,
)

__all__ = [
    "FindSourceQuery",
    "ListActiveSourcesQuery",
    "FindFeedQuery",
    "ListFeedsQuery",
    "FindArticleQuery",
    "ListArticlesQuery",
]
